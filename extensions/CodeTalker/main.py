import copy
import os
import random
import re
from typing import List

from modules.plugin_base import AbstractPlugin

__all__ = ["CodeTalker"]


class CodeTalker(AbstractPlugin):
    CONFIG_DETECTED_KEYWORD = "detected_keyword"
    CONFIG_SECRETS = "secrets"
    CONFIG_SECRETS_APPID = f"{CONFIG_SECRETS}/appID"
    CONFIG_SECRETS_APIKEY = f"{CONFIG_SECRETS}/apiKey"
    CONFIG_SECRETS_API_SECRETS = f"{CONFIG_SECRETS}/apiSecrets"
    CONFIG_API_VERSION = "ApiVersion"
    CONFIG_PRE_APPEND_HISTORY = "pre_append_history"
    CONFIG_DICTIONARY_PATH = "dictionary_path"
    CONFIG_RE_GENERATE_PROBABILITY = "re_generate_probability"

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
        return "0.0.3"

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
            self.CONFIG_PRE_APPEND_HISTORY,
            [],
        )
        self._config_registry.register_config(
            self.CONFIG_DICTIONARY_PATH, f"{self._get_config_parent_dir()}/fuzzy_dictionary.json"
        )
        self._config_registry.register_config(self.CONFIG_RE_GENERATE_PROBABILITY, 0.3)

    def install(self):
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.event.message import GroupMessage
        from graia.ariadne.model import Group
        from sparkdesk_api.core import SparkAPI
        from graia.ariadne.util.cooldown import CoolDown

        from .fuzzy import FuzzyDictionary

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast
        reg = re.compile(r"(^.*)[?？]$")
        # 默认api接口版本为1.5，开启v2.0版本只需指定 version=2.1 即可
        sparkAPI = SparkAPI(
            app_id=self._config_registry.get_config(self.CONFIG_SECRETS_APPID),
            api_secret=self._config_registry.get_config(self.CONFIG_SECRETS_API_SECRETS),
            api_key=self._config_registry.get_config(self.CONFIG_SECRETS_APIKEY),
            version=self._config_registry.get_config(self.CONFIG_API_VERSION),
        )
        fuzzy_dictionary = FuzzyDictionary(save_path=self._config_registry.get_config(self.CONFIG_DICTIONARY_PATH))
        print(f"Loading Fuzzy Dictionary Size:{len(fuzzy_dictionary.dictionary.keys())}")
        history = copy.deepcopy(self._config_registry.get_config(self.CONFIG_PRE_APPEND_HISTORY))

        @bord_cast.receiver(
            GroupMessage,
            dispatchers=[CoolDown(1)],
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

            search: List[str] = fuzzy_dictionary.search(words)

            if random.random() <= self._config_registry.get_config(self.CONFIG_RE_GENERATE_PROBABILITY) or not search:
                response: str = sparkAPI.chat(query=words, history=history, max_tokens=40)
                if response:
                    fuzzy_dictionary.register_key_value(words, response)
                    fuzzy_dictionary.save_to_json()
                else:
                    response = "a"
                print(f"Request Response: {response}")
            else:
                response = random.choice(search)
                print(f"Use Cache: {response}")

            await ariadne_app.send_group_message(group, response)
