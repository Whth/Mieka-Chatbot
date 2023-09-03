import os
from types import MappingProxyType
from typing import Union, List, Dict

from modules.plugin_base import AbstractPlugin

ROOT: str = os.path.abspath(os.path.dirname(__file__))

EXTENSION_DIR: str = "extensions"
MAIN = ".main"
CONFIG_FILE_NAME: str = "config.json"
REQUIREMENTS_FILE_NAME: str = "requirements.txt"
PluginsView = MappingProxyType[str, AbstractPlugin]
Value = Union[str, int, float, List, Dict]
CONFIG_PATH_PATTERN = r"[\\/]"
