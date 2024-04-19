@echo off
set PYTHON_PATH=V:\Matrix\LANG_CORE\python311\python.exe

if not exist venv (
    %PYTHON_PATH% -m venv venv
)




call ./venv/Scripts/activate

echo Installing core deps
pip install -q -r requirements.txt
echo Booting
python launch.py %*

