import os
from typing import Dict

from modules.plugin_base import AbstractPlugin

__all__ = ["BaiduTranslater"]


class BaiduTranslater(AbstractPlugin):
    CONFIG_APP_ID = "app_id"
    CONFIG_APP_KEY = "app_key"
    CONFIG_API_URL = "api_url"

    translater = None

    CONFIG_TRANSLATE_KEYWORD = "TranslateKeyword"

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
        return "0.0.2"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_APP_ID, "replace with baidu translate app_id")
        self._config_registry.register_config(self.CONFIG_APP_KEY, "replace with baidu translate app_key")
        self._config_registry.register_config(self.CONFIG_API_URL, "http://api.fanyi.baidu.com/api/trans/vip/translate")
        self._config_registry.register_config(self.CONFIG_TRANSLATE_KEYWORD, "翻译")

    def install(self):
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.message.parser.base import DetectPrefix
        from graia.ariadne.model import Group
        from .translater import Translater
        from modules.config_utils import ConfigClient

        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast
        self.__register_all_config()
        self._config_registry.load_config()
        self.translater = Translater(
            appid=self._config_registry.get_config(self.CONFIG_APP_ID),
            appkey=self._config_registry.get_config(self.CONFIG_APP_KEY),
            url=self._config_registry.get_config(self.CONFIG_API_URL),
        )

        def _trans_partial(to_lang: str, query: str) -> str:
            return self.translater.translate(to_lang, query)

        cmd_syntax_tree: Dict = {self._config_registry.get_config(self.CONFIG_TRANSLATE_KEYWORD): _trans_partial}
        client = ConfigClient(cmd_syntax_tree)

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[DetectPrefix(prefix=self._config_registry.get_config(self.CONFIG_TRANSLATE_KEYWORD))],
        )
        async def translate(group: Group, message: MessageChain):
            """
            Asynchronous function that translates a message in a group.

            Args:
                group (Group): The group where the message was sent.
                message (MessageChain): The message to be translated.

            Returns:
                None
            """
            result = client.interpret(str(message))

            await ariadne_app.send_message(group, message=f"翻译结果:\n\t{result}")

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
