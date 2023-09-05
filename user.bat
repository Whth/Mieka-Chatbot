@echo off
set PYTHON_PATH=python

if not exist venv (
    %PYTHON_PATH% -m venv venv
)




call venv\Scripts\activate
start cmd /c "python -m pip install -r requirements.txt"
start cmd /c "python launch.py"
