@echo off

call venv/scripts/activate
start cmd /c "python -m pip install -r requirements.txt"
start cmd /c "python launch.py"
