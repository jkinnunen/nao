#Nao (NVDA Advanced OCR) is an addon that improves the standard OCR capabilities that NVDA provides on modern Windows versions.
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Last update 2021-12-21
#Copyright (C) 2021 Alessandro Albano, Davide De Carne and Simone Dal Maso

import api
import winGDI
import wx
import time
import queueHandler
import winVersion
from logHandler import log
from contentRecog import uwpOcr, recogUi, LinesWordsResult
from .. speech import speech
from .. generic import screen
from .. import language

language.initTranslation()

class OCRResultPageOffset():
	def __init__(self, start, length):
		self.start = start
		self.end = start + length

class OCR:
	def is_uwp_ocr_available():
		return winVersion.isUwpOcrAvailable()

	def recognize_screenshot(on_start=None, on_finish=None, on_finish_arg=None):
		if isinstance(api.getFocusObject(), recogUi.RecogResultNVDAObject):
			# Translators: Reported when content recognition (e.g. OCR) is attempted,
			# but the user is already reading a content recognition result.
			speech.message(_N("Already in a content recognition result"))
			return False
		if not OCR.is_uwp_ocr_available():
			# Translators: Reported when Windows OCR is not available.
			speech.message(_N("Windows OCR not available"))
			return False
		if screen.have_curtain():
			# Translators: Reported when screen curtain is enabled.
			speech.message(_N("Please disable screen curtain before using Windows OCR."))
			return False
		if on_start:
			on_start()
		pixels, width, height = screen.take_snapshot_pixels()
		recognizer = uwpOcr.UwpOcr()
		try:
			imgInfo = recogUi.RecogImageInfo.createFromRecognizer(0, 0, width, height, recognizer)
		except ValueError:
			# Translators: Reporting an error during recognition (e.g. OCR).
			speech.message(_("Internal conversion error"))
			return False
		if recogUi._activeRecog:
			recogUi._activeRecog.cancel()
			recogUi._activeRecog = None
		recogUi._activeRecog = recognizer
		def h(result):
			if isinstance(result, Exception):
				recogUi._activeRecog = None
				# Translators: Reporting when recognition (e.g. OCR) fails.
				log.error(_N("Recognition failed") + ': ' + str(result))
				speech.queue_message(_N("Recognition failed"))
				if on_finish:
					if on_finish_arg is None:
						on_finish(success=False)
					else:
						on_finish(success=False, arg=on_finish_arg)
				return
			recogUi._recogOnResult(result)
			recogUi._activeRecog = None
			if on_finish:
				if on_finish_arg is None:
					on_finish(success=True)
				else:
					on_finish(success=True, arg=on_finish_arg)
		try:
			recognizer.recognize(pixels, imgInfo, h)
			return True
		except Exception as e:
			h(e)
		return False

	def __init__(self):
		self.clear()

	def clear(self):
		self.source_count = 0
		self.bmp_list = []
		self.results = []
		self.pages_offset = []
		self.on_finish = None
		self.on_finish_arg = None
		self.on_progress = None
		self.progress_timeout = 1
		self.last_progress = 0
		self.source_file = None
		self.must_abort = False

	def abort(self):
		self.must_abort = True

	def recognize_files(self, source_file, source_file_list, on_start=None, on_finish=None, on_finish_arg=None, on_progress=None, progress_timeout=0):
		if not OCR.is_uwp_ocr_available():
			# Translators: Reported when Windows OCR is not available.
			speech.queue_message(_N("Windows OCR not available"))
			if on_finish:
				if on_finish_arg is None:
					on_finish(source_file=source_file, result=None, pages_offset=None)
				else:
					on_finish(source_file=source_file, result=None, pages_offset=None, arg=on_finish_arg)
			return
		if recogUi._activeRecog:
			recogUi._activeRecog.cancel()
			recogUi._activeRecog = None
		self.clear()
		self.source_file = source_file
		self.on_finish = on_finish
		self.on_finish_arg = on_finish_arg
		self.on_progress = on_progress
		self.progress_timeout = progress_timeout
		self.source_count = len(source_file_list)
		self.last_progress = time.time()
		if on_start:
			on_start(source_file=self.source_file)
		for f in source_file_list:
			bmp = wx.Bitmap(f)
			self.bmp_list.append(bmp)
		if not self._recognize_next_page():
			if on_finish:
				if on_finish_arg is None:
					on_finish(source_file=source_file, result=None, pages_offset=None)
				else:
					on_finish(source_file=source_file, result=None, pages_offset=None, arg=on_finish_arg)
			self.clear()

	def _recognize_next_page(self):
		if self.must_abort: return False
		remaining = len(self.bmp_list)
		now = time.time()
		if now - self.last_progress >= self.progress_timeout:
			self.last_progress = now
			if self.on_progress:
				self.on_progress(self.source_count - remaining, self.source_count)
		if remaining > 0:
			recognizer = uwpOcr.UwpOcr()
			bmp = self.bmp_list.pop(0)
			width, height = bmp.Size.Get()
			imgInfo = recogUi.RecogImageInfo.createFromRecognizer(0, 0, width, height, recognizer)
			pixels = (winGDI.RGBQUAD*width*height)()
			bmp.CopyToBuffer(pixels, format=wx.BitmapBufferFormat_ARGB32)
			recogUi._activeRecog = recognizer
			try:
				recognizer.recognize(pixels, imgInfo, self._on_recognize_result)
				return True
			except Exception as e:
				self._on_recognize_result(e)
		return False

	def _on_recognize_result(self, result):
		recogUi._activeRecog = None
		# This might get called from a background thread, so any UI calls must be queued to the main thread.
		if isinstance(result, Exception):
			# Translators: Reporting when recognition (e.g. OCR) fails.
			log.error(_N("Recognition failed") + ': ' + str(result))
			speech.queue_message(_N("Recognition failed"))
			if self.on_finish:
				if self.on_finish_arg is None:
					self.on_finish(source_file=self.source_file, result=result, pages_offset=None)
				else:
					self.on_finish(source_file=self.source_file, result=result, pages_offset=None, arg=self.on_finish_arg)
			self.clear()
			return
		
		if len(self.pages_offset) == 0:
			self.pages_offset.append(OCRResultPageOffset(0, result.textLen))
		else:
			self.pages_offset.append(OCRResultPageOffset(self.pages_offset[len(self.pages_offset) - 1].end, result.textLen))
		
		# Result is a LinesWordsResult, we store all pages data objects that we will merge later in a single LinesWordsResult
		for line in result.data:
			self.results.append(line)
		
		if not self._recognize_next_page():
			# No more pages
			def h():
				if self.on_finish:
					if self.must_abort:
						if self.on_finish_arg is None:
							self.on_finish(source_file=self.source_file, result=None, pages_offset=None)
						else:
							self.on_finish(source_file=self.source_file, result=None, pages_offset=None, arg=self.on_finish_arg)
					else:
						if self.on_finish_arg is None:
							self.on_finish(source_file=self.source_file, result=LinesWordsResult(self.results, result.imageInfo), pages_offset=self.pages_offset)
						else:
							self.on_finish(source_file=self.source_file, result=LinesWordsResult(self.results, result.imageInfo), pages_offset=self.pages_offset, arg=self.on_finish_arg)
				self.clear()
			queueHandler.queueFunction(queueHandler.eventQueue, h)