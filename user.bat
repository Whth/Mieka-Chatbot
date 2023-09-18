@echo off
set PYTHON_PATH=python

if not exist venv (
    %PYTHON_PATH% -m venv venv
)




call venv\Scripts\activate
%PYTHON_PATH% -m pip install -r requirements.txt
%PYTHON_PATH% launch.py

