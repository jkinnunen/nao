@echo off
setlocal

set "VENV_DIR=.venv"
set "REQ_FILE=requirements.txt"

where py >nul 2>nul
if %errorlevel%==0 (
	set "PYTHON_CMD=py -3.10"
) else (
	set "PYTHON_CMD=python"
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
	echo Creating virtual environment in %VENV_DIR%...
	%PYTHON_CMD% -m venv "%VENV_DIR%"
	if errorlevel 1 exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 exit /b 1

python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

if exist "%REQ_FILE%" (
	python -m pip install -r "%REQ_FILE%"
	if errorlevel 1 exit /b 1
)

echo Virtual environment ready and activated.
