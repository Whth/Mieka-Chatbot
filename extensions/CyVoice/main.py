import os
from typing import List

from modules.plugin_base import AbstractPlugin

__all__ = ["CyVoice"]


class CyVoice(AbstractPlugin):
    __READ_CMD = "read"
    __CHANGE_CV_CMD = "change"
    __LIST_CV_CMD = "list"
    __CURRENT_CV_CMD = "current"
    __CONFIG_CMD = "config"
    __CONFIG_SET_CMD = "set"
    __CONFIG_LIST_CMD = "list"

    CONFIG_NOISE = "Noise"
    CONFIG_NOISE_W = "NoiseW"
    CONFIG_MAX = "Max"

    CONFIG_DETECTED_KEYWORD = "Keyword"
    CONFIG_USED_CV_INDEX = "UsedCVIndex"
    CONFIG_API_HOST_URL = "ApiHostUrl"
    CONFIG_TEMP_FILE_DIR_PATH = "TempFileDirPath"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "CyVoice"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "use simple-vits-api to read sentence"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "cv")
        self._config_registry.register_config(self.CONFIG_API_HOST_URL, "http://127.0.0.1:23456/voice")
        self._config_registry.register_config(self.CONFIG_USED_CV_INDEX, 0)
        self._config_registry.register_config(self.CONFIG_TEMP_FILE_DIR_PATH, f"{self._get_config_parent_dir()}/temp")

        self._config_registry.register_config(self.CONFIG_NOISE, 0.667)
        self._config_registry.register_config(self.CONFIG_NOISE_W, 0.8)
        self._config_registry.register_config(self.CONFIG_MAX, 50)

    def install(self):
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.message.element import Voice
        from graia.ariadne.message.parser.base import DetectPrefix
        from graia.ariadne.model import Group

        from modules.config_utils import ConfigClient

        from .api import voice_vits, voice_speakers, get_voice_speakers

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast
        temp_dir: str = self._config_registry.get_config(self.CONFIG_TEMP_FILE_DIR_PATH)
        os.makedirs(temp_dir, exist_ok=True)
        api_host_url: str = self._config_registry.get_config(self.CONFIG_API_HOST_URL)
        # TODO should decouple api host url

        configurable_options: List[str] = [
            self.CONFIG_NOISE,
            self.CONFIG_NOISE_W,
            self.CONFIG_MAX,
        ]

        def list_out_configs() -> str:
            """
            Returns a string that lists out the configurations.

            Returns:
                str: The string that lists out the configurations.
            """
            result_string = ""
            for option in configurable_options:
                result_string += f"{option} = {self._config_registry.get_config(option)}\n"
            return result_string

        def set_float_config(key: str, value: float) -> str:
            """
            Set a boolean configuration value.

            Args:
                key (str): The key of the configuration value.
                value (int): The value to be set.

            Returns:
                str: A string indicating the result of the operation.
            """
            result_string = f"setting [{key}] to [{value}]"

            self._config_registry.set_config(key, value)
            return result_string

        def change_cv_index(index: int) -> str:
            temp = self._config_registry.get_config(self.CONFIG_USED_CV_INDEX)
            self._config_registry.set_config(self.CONFIG_USED_CV_INDEX, index)
            return f"change cv index [{temp}] to [{index}]"

        def get_current_cv() -> str:
            cv_id: int = self._config_registry.get_config(self.CONFIG_USED_CV_INDEX)
            speaker_names = get_voice_speakers()
            return f"Current:\n{cv_id:<4}|{speaker_names[cv_id]}"

        def read_sentence(sentence: str) -> Voice:
            save_path = voice_vits(
                sentence, id=self._config_registry.get_config(self.CONFIG_USED_CV_INDEX), save_dir=temp_dir
            )
            return Voice(path=save_path)

        tree = {
            self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD): {
                self.__LIST_CV_CMD: voice_speakers,
                self.__CHANGE_CV_CMD: change_cv_index,
                self.__READ_CMD: read_sentence,
                self.__CURRENT_CV_CMD: get_current_cv,
                self.__CONFIG_CMD: {
                    self.__CONFIG_LIST_CMD: list_out_configs,
                    self.__CONFIG_SET_CMD: set_float_config,
                },
            }
        }
        client = ConfigClient(tree)

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[DetectPrefix(prefix=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD))],
        )
        async def cyvoice_client(group: Group, message: MessageChain):
            result = client.interpret(str(message))
            await ariadne_app.send_message(group, result)
