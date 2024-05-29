@echo off
set PYTHON_PATH=python

if not exist venv (
    %PYTHON_PATH% -m venv venv
)




call ./venv/Scripts/activate

echo Installing core deps
pip install -q -r requirements.txt
echo Booting
python launch.py %*

pause