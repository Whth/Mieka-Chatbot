import copy
import random
from functools import partial
from typing import List

from sparkdesk_api.core import SparkAPI

from modules.shared import (
    get_pwd,
    AbstractPlugin,
    ExecutableNode,
    Permission,
    PermissionCode,
    required_perm_generator,
    RequiredPermission,
)
from .fuzzy import FuzzyDictionary

__all__ = ["CodeTalker"]


class CMD:
    CHAT: str = "chat"


class CodeTalker(AbstractPlugin):
    CONFIG_SECRETS = "secrets"
    CONFIG_SECRETS_APPID = f"{CONFIG_SECRETS}/appID"
    CONFIG_SECRETS_APIKEY = f"{CONFIG_SECRETS}/apiKey"
    CONFIG_SECRETS_API_SECRETS = f"{CONFIG_SECRETS}/apiSecrets"
    CONFIG_API_VERSION = "ApiVersion"
    CONFIG_PRE_APPEND_HISTORY = "pre_append_history"
    CONFIG_DICTIONARY_PATH = "dictionary_path"
    CONFIG_RE_GENERATE_PROBABILITY = "re_generate_probability"
    CONFIG_MAX_TOKENS = "max_tokens"

    DefaultConfig = {
        CONFIG_SECRETS_APPID: "your appid",
        CONFIG_SECRETS_APIKEY: "your api key",
        CONFIG_SECRETS_API_SECRETS: "your api secret",
        CONFIG_API_VERSION: 2.1,
        CONFIG_PRE_APPEND_HISTORY: [],
        CONFIG_DICTIONARY_PATH: f"{get_pwd()}/fuzzy_dictionary.json",
        CONFIG_RE_GENERATE_PROBABILITY: 0.3,
        CONFIG_MAX_TOKENS: 150,
    }

    @classmethod
    def get_plugin_name(cls) -> str:
        return "CodeTalker"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "use Spark 2.0 api"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.4"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 默认api接口版本为1.5，开启v2.0版本只需指定 version=2.1 即可
        self.sparkAPI = SparkAPI(
            app_id=self._config_registry.get_config(self.CONFIG_SECRETS_APPID),
            api_secret=self._config_registry.get_config(self.CONFIG_SECRETS_API_SECRETS),
            api_key=self._config_registry.get_config(self.CONFIG_SECRETS_APIKEY),
            version=self._config_registry.get_config(self.CONFIG_API_VERSION),
        )

    def install(self):
        fuzzy_dictionary = FuzzyDictionary(save_path=self._config_registry.get_config(self.CONFIG_DICTIONARY_PATH))
        print(f"Loading Fuzzy Dictionary Size:{len(fuzzy_dictionary.dictionary.keys())}")
        history = copy.deepcopy(self._config_registry.get_config(self.CONFIG_PRE_APPEND_HISTORY))
        su_perm = Permission(id=PermissionCode.SuperPermission.value, name=self.get_plugin_name())
        req_perm: RequiredPermission = required_perm_generator(
            target_resource_name=self.get_plugin_name(), super_permissions=[su_perm]
        )

        def _talk(message: str, max_tokens: int = 0) -> str:
            # Search for similar words in the fuzzy dictionary
            search: List[str] = fuzzy_dictionary.search(message)

            # If the random number is less than or equal to the re-generate probability
            # or no similar words are found in the dictionary
            if random.random() <= self._config_registry.get_config(self.CONFIG_RE_GENERATE_PROBABILITY) or not search:
                max_tokens = max_tokens if max_tokens else self._config_registry.get_config(self.CONFIG_MAX_TOKENS)
                # Generate a response using the Spark API
                response: str = self.sparkAPI.chat(
                    query=message,
                    history=history,
                    max_tokens=max_tokens,
                )
                if response:
                    # Register the generated response in the fuzzy dictionary
                    fuzzy_dictionary.register_key_value(message, response)
                    fuzzy_dictionary.save_to_json()
                else:
                    response = "a"
                print(f"Request Response: {response}")
            else:
                # Select a random response from the search results
                response = random.choice(search)
                print(f"Use Cache: {response}")
            return response

        tree = ExecutableNode(
            name=CMD.CHAT,
            required_permissions=req_perm,
            source=_talk,
            help_message=f"{self.get_plugin_name()} - {self.get_plugin_description()}",
        )
        self._auth_manager.add_perm_from_req(req_perm)
        self._root_namespace_node.add_node(tree)

    def chat(self, string: str) -> str:
        spark_par = partial(
            SparkAPI,
            app_id=self._config_registry.get_config(self.CONFIG_SECRETS_APPID),
            api_secret=self._config_registry.get_config(self.CONFIG_SECRETS_API_SECRETS),
            api_key=self._config_registry.get_config(self.CONFIG_SECRETS_APIKEY),
        )

        self._config_registry.get_config(self.CONFIG_API_VERSION),
        available_versions = {3.1, 2.1, 1.5}
        for ver in available_versions:
            stdout = spark_par(version=ver).chat(
                query=string, max_tokens=self.config_registry.get_config(self.CONFIG_MAX_TOKENS)
            )
            if stdout:
                return stdout
        return ""
