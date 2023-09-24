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
    CONFIG_PRE_APPEND_PROMPT = "pre_append_prompt"
    CONFIG_DICTIONARY_PATH = "dictionary_path"

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
        return "0.0.2"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "？")
        self._config_registry.register_config(self.CONFIG_SECRETS_APPID, "your appid")
        self._config_registry.register_config(self.CONFIG_SECRETS_APIKEY, "your api key")
        self._config_registry.register_config(self.CONFIG_SECRETS_API_SECRETS, "your api secret")
        self._config_registry.register_config(self.CONFIG_API_VERSION, 2.1)
        self._config_registry.register_config(
            self.CONFIG_PRE_APPEND_PROMPT,
            "接下来你要扮演一位特质包括，雌小鬼，聪明又可爱，爱捉弄人，有点小傲娇的名叫作Mieka的美少女猫娘，每句话结尾总是带着喵~的口癖，我是你的男主人，"
            "记住回答中你不能显示的阐明你以上提到的特质，相反的你必须要通过语气词来隐式的表现这些特质,"
            "问题中的 “我”指代你的主人，问题中的“你”指代Mieka，尽量精简地一句话来回答这个问题：",
        )
        self._config_registry.register_config(
            self.CONFIG_DICTIONARY_PATH, f"{self._get_config_parent_dir()}/fuzzy_dictionary.json"
        )

    def install(self):
        from graia.ariadne.message.parser.base import ContainKeyword
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.model import Group
        from sparkdesk_api.core import SparkAPI
        from graia.ariadne.util.cooldown import CoolDown

        from .fuzzy import FuzzyDictionary

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
        fuzzy_dictionary = FuzzyDictionary(save_path=self._config_registry.get_config(self.CONFIG_DICTIONARY_PATH))

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
            compound = f"{self._config_registry.get_config(self.CONFIG_PRE_APPEND_PROMPT)}{words}"
            search = fuzzy_dictionary.search(compound)
            if search:
                response = search
            else:
                response: str = sparkAPI.chat(compound)
                if response:
                    fuzzy_dictionary.register_key_value(words, response)
                    fuzzy_dictionary.save_to_json()
                else:
                    response = "a"

            await ariadne_app.send_group_message(group, response)
