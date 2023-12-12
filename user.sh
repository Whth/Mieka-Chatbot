#!/bin/bash

PYTHON_PATH=python

if [ ! -d "venv" ]; then
  $PYTHON_PATH -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
python launch.py "$@"
