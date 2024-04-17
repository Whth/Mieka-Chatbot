@echo off
set PYTHON_PATH=python

if not exist venv (
    %PYTHON_PATH% -m venv venv
)




set V_PYTHON=venv\Scripts\python.exe
%V_PYTHON% -m pip install -q -r requirements.txt
%V_PYTHON% launch.py %*

