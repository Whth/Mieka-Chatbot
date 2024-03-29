import pathlib

from typing import Union, List, Dict

ROOT: str = str(pathlib.Path(__file__).parent)
CONFIG_DIR: str = "config"
EXTENSION_DIR: str = "extensions"
EXTENSION_CONFIG_DIR: str = f"{CONFIG_DIR}/{EXTENSION_DIR}"
CONFIG_FILE_NAME: str = "config.json"
REQUIREMENTS_FILE_NAME: str = "requirements.txt"
USER_BATCH_SCRIPT_PATH = str(pathlib.Path(f"{ROOT}/user.bat"))
Value = Union[str, int, float, List, Dict, bool]
CONFIG_PATH_PATTERN = r"[\/]"


pathlib.Path(EXTENSION_CONFIG_DIR).mkdir(parents=True, exist_ok=True)
