@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Creando entorno virtual...
    python -m venv .venv
    .venv\Scripts\pip install -q -r requirements.txt
)
start "" .venv\Scripts\pythonw.exe gui.py
