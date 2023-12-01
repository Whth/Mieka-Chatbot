from typing import Dict

from modules.shared import AbstractPlugin


class Ecno(AbstractPlugin):
    CONFIG_DETECTED_KEYWORD = "detected_keyword"

    DefaultConfig: Dict = {CONFIG_DETECTED_KEYWORD: "hello"}

    @classmethod
    def get_plugin_name(cls) -> str:
        return "Ecno"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "Economical Calculator"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "Whth"

    def install(self):
        pass
