import os

from modules.plugin_base import AbstractPlugin
from .translater import Translater

__all__ = ["BaiduTranslater"]


class BaiduTranslater(AbstractPlugin):
    CONFIG_APPID = "appid"
    CONFIG_APPKEY = "appkey"
    CONFIG_API_URL = "api_url"

    translater = None

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "BaiduTranslater"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "A translation plugin using baidu api"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_APPID, "replace with baidu translate appid")
        self._config_registry.register_config(self.CONFIG_APPKEY, "replace with baidu translate appkey")
        self._config_registry.register_config(self.CONFIG_API_URL, "http://api.fanyi.baidu.com/api/trans/vip/translate")

    def install(self):
        self.__register_all_config()
        self._config_registry.load_config()
        self.translater = Translater(
            appid=self._config_registry.get_config(self.CONFIG_APPID),
            appkey=self._config_registry.get_config(self.CONFIG_APPKEY),
            url=self._config_registry.get_config(self.CONFIG_API_URL),
        )

        # TODO mount a translating service

    def translate(self, to_lang: str, query: str, from_lang: str = "auto"):
        """
        Wrapper for baidu translates
        Args:
            to_lang ():
            query ():
            from_lang ():

        Returns:

        """
        return self.translater.translate(to_lang, query, from_lang)
