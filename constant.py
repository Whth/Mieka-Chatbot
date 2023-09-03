import os
from typing import Union, List, Dict

ROOT: str = os.path.abspath(os.path.dirname(__file__))

EXTENSION_DIR: str = "extensions"
MAIN = ".main"
CONFIG_FILE_NAME: str = "config.json"
REQUIREMENTS_FILE_NAME: str = "requirements.txt"

Value = Union[str, int, float, List, Dict]
CONFIG_PATH_PATTERN = r"[\\/]"
