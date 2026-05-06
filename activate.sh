#!/usr/bin/env sh
set -eu

VENV_DIR=".venv"
REQ_FILE="requirements.txt"

if command -v python3 >/dev/null 2>&1; then
	PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
	PYTHON_CMD="python"
else
	echo "Python not found in PATH." >&2
	exit 1
fi

if [ ! -x "$VENV_DIR/Scripts/python.exe" ] && [ ! -x "$VENV_DIR/bin/python" ]; then
	echo "Creating virtual environment in $VENV_DIR..."
	"$PYTHON_CMD" -m venv "$VENV_DIR"
fi

if [ -f "$VENV_DIR/bin/activate" ]; then
	# POSIX venv layout
	. "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
	# Git Bash / MSYS on Windows may use the Windows layout
	. "$VENV_DIR/Scripts/activate"
elif [ -f "$VENV_DIR/Scripts/activate.bat" ]; then
	echo "Virtual environment created with Windows layout. Use activate.bat from CMD for persistent activation." >&2
	"$VENV_DIR/Scripts/python.exe" -m pip install --upgrade pip
	"$VENV_DIR/Scripts/python.exe" -m pip install -r "$REQ_FILE"
	exit 0
else
	echo "Unable to locate the virtual environment activation script." >&2
	exit 1
fi

python -m pip install --upgrade pip
python -m pip install -r "$REQ_FILE"

echo "Virtual environment ready and activated in the current shell."
