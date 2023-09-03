import os
from types import MappingProxyType
from typing import Union, List, Dict

from modules.plugin_base import AbstractPlugin

PACKAGE_ROOT: str = os.path.abspath(os.path.dirname(__file__))
MAIN = ".main"
EXTENSION_DIR: str = "extensions"
PluginsView = MappingProxyType[str, AbstractPlugin]
Value = Union[str, int, float, List, Dict]
CONFIG_PATH_PATTERN = r"[\\/]"
