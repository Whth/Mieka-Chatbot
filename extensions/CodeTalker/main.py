import os
import re

from modules.plugin_base import AbstractPlugin

__all__ = ["CodeTalker"]


class CodeTalker(AbstractPlugin):
    CONFIG_DETECTED_KEYWORD = "detected_keyword"
    CONFIG_SECRETS = "secrets"
    CONFIG_SECRETS_APPID = f"{CONFIG_SECRETS}/appID"
    CONFIG_SECRETS_APIKEY = f"{CONFIG_SECRETS}/apiKey"
    CONFIG_SECRETS_API_SECRETS = f"{CONFIG_SECRETS}/apiSecrets"
    CONFIG_API_VERSION = "ApiVersion"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "CodeTalker"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "use Spark 2.0 api"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "？")
        self._config_registry.register_config(self.CONFIG_SECRETS_APPID, "your appid")
        self._config_registry.register_config(self.CONFIG_SECRETS_APIKEY, "your api key")
        self._config_registry.register_config(self.CONFIG_SECRETS_API_SECRETS, "your api secret")
        self._config_registry.register_config(self.CONFIG_API_VERSION, 2.1)

    def install(self):
        from graia.ariadne.message.parser.base import ContainKeyword
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.model import Group
        from sparkdesk_api.core import SparkAPI
        from graia.ariadne.util.cooldown import CoolDown

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast
        reg = re.compile(r"^(?=.*[^\s?])[^?]+[?？]$")
        # 默认api接口版本为1.5，开启v2.0版本只需指定 version=2.1 即可
        sparkAPI = SparkAPI(
            app_id=self._config_registry.get_config(self.CONFIG_SECRETS_APPID),
            api_secret=self._config_registry.get_config(self.CONFIG_SECRETS_API_SECRETS),
            api_key=self._config_registry.get_config(self.CONFIG_SECRETS_APIKEY),
            version=self._config_registry.get_config(self.CONFIG_API_VERSION),
        )

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[
                ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD)),
            ],
            dispatchers=[CoolDown(10)],
        )
        async def talk(group: Group, message: MessageChain):
            """
            Asynchronous function that handles group messages.

            Args:
                group (Group): The group object representing the group where the message was sent.
                message (MessageChain): The message chain object representing the message received.

            Returns:
                None

            Raises:
                None
            """
            words = str(message)

            if not re.match(reg, string=words):
                return

            response: str = sparkAPI.chat(words)

            if not response:
                response = "a"
            await ariadne_app.send_group_message(group, response)
