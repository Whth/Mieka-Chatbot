import copy
import random
from functools import partial
from typing import List

from sparkdesk_api.core import SparkAPI
from sparkdesk_api.utils import VERSIONS

from modules.shared import get_pwd, AbstractPlugin, ExecutableNode, EnumCMD, CmdBuilder, NameSpaceNode
from .external_gpt import run_all, api
from .fuzzy import FuzzyDictionary

__all__ = ["CodeTalker"]

VERSIONS.add(3.5)


class CMD(EnumCMD):
    chat = ["ct", "fed"]
    chatcfg = ["ctc", "ctcfg"]
    list = ["l", "ls"]
    set = ["s", "st"]
    cache = ["c", "cac"]
    clear = ["cls", "clr"]
    size = ["s", "sz"]
    talk = ["dd"]


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
    CONFIG_SILENT_FEEDBACK = "silent_feedback"
    DefaultConfig = {
        CONFIG_SECRETS_APPID: "your appid",
        CONFIG_SECRETS_APIKEY: "your api key",
        CONFIG_SECRETS_API_SECRETS: "your api secret",
        CONFIG_API_VERSION: 2.1,
        CONFIG_DICTIONARY_PATH: f"{get_pwd()}/fuzzy_dictionary.json",
        CONFIG_RE_GENERATE_PROBABILITY: 0.3,
        CONFIG_MAX_TOKENS: 150,
        CONFIG_PRE_APPEND_HISTORY: [],
        CONFIG_SILENT_FEEDBACK: [
            "I'm sorry, I don't understand.",
            "I'm sorry, I can't help you.",
            "I don't have an answer for that.",
            "I don't know what you mean.",
            "I don't understand.",
            "I can't help you.",
            "NG",
        ],
    }

    @classmethod
    def get_plugin_name(cls) -> str:
        return "CodeTalker"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "use Spark api"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.5"

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

        configurable = {
            self.CONFIG_API_VERSION,
            self.CONFIG_RE_GENERATE_PROBABILITY,
            self.CONFIG_MAX_TOKENS,
        }
        builder = CmdBuilder(
            config_getter=self.config_registry.get_config, config_setter=self.config_registry.set_config
        )

        def _talk(*message_token: str) -> str:
            """
            Executes the _talk function to generate a response based on the given message tokens.

            Args:
                *message_token (str): The message tokens to be processed.

            Returns:
                str: The generated response based on the message tokens.
            """
            message = " ".join(message_token)
            # Search for similar words in the fuzzy dictionary
            search: List[str] = fuzzy_dictionary.search(message)

            # If the random number is less than or equal to the re-generate probability
            # or no similar words are found in the dictionary
            if random.random() <= self._config_registry.get_config(self.CONFIG_RE_GENERATE_PROBABILITY) or not search:
                max_tokens = self._config_registry.get_config(self.CONFIG_MAX_TOKENS)
                # Generate a response using the Spark API
                response: str = self.sparkAPI.chat(
                    query=message,
                    history=copy.deepcopy(self._config_registry.get_config(self.CONFIG_PRE_APPEND_HISTORY)),
                    max_tokens=max_tokens,
                )
                if response:
                    # Register the generated response in the fuzzy dictionary
                    fuzzy_dictionary.register_key_value(message, response)
                    fuzzy_dictionary.save_to_json()
                else:
                    response = random.choice(self.config_registry.get_config(self.CONFIG_SILENT_FEEDBACK))
                print(f"Request Response: {response}")
            else:
                # Select a random response from the search results
                response = random.choice(search)
                print(f"Use Cache: {response}")

            return response

        tree = ExecutableNode(
            **CMD.chat.export(),
            required_permissions=self.required_permission,
            source=_talk,
        )

        self.root_namespace_node.add_node(tree)

        config_tree = NameSpaceNode(
            **CMD.chatcfg.export(),
            required_permissions=self.required_permission,
            help_message="Config for CodeTalker",
            children_node=[
                ExecutableNode(**CMD.set.export(), source=builder.build_group_setter_for(configurable)),
                ExecutableNode(**CMD.list.export(), source=builder.build_list_out_for(configurable)),
                NameSpaceNode(
                    **CMD.cache.export(),
                    help_message="CodeTalker cache utils",
                    children_node=[
                        ExecutableNode(
                            **CMD.clear.export(),
                            source=lambda: fuzzy_dictionary.dictionary.clear(),
                            help_message="Clear CodeTalker cache",
                        ),
                        ExecutableNode(
                            **CMD.size.export(),
                            source=lambda: f"CodeTalker cache size: {len(fuzzy_dictionary.dictionary)}",
                            help_message="Get CodeTalker cache size",
                        ),
                    ],
                ),
            ],
        )
        self.root_namespace_node.add_node(
            ExecutableNode(
                **CMD.talk.export(),
                source=api,
                help_message="External GPT chat",
            ),
        )
        self.root_namespace_node.add_node(config_tree)

    def chat(self, string: str) -> str:
        """
        Performs a chat operation using the SparkAPI.

        Args:
            string (str): The input string for the chat operation.

        Returns:
            str: The output generated by the chat operation.

        """
        spark_par = partial(
            SparkAPI,
            app_id=self._config_registry.get_config(self.CONFIG_SECRETS_APPID),
            api_secret=self._config_registry.get_config(self.CONFIG_SECRETS_API_SECRETS),
            api_key=self._config_registry.get_config(self.CONFIG_SECRETS_APIKEY),
        )

        self._config_registry.get_config(self.CONFIG_API_VERSION),

        for ver in sorted(list(VERSIONS), reverse=True):
            stdout = spark_par(version=ver).chat(
                query=string, max_tokens=self.config_registry.get_config(self.CONFIG_MAX_TOKENS)
            )
            if stdout:
                return stdout
        return ""
