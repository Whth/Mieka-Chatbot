import os
from typing import List, Callable, Optional

from modules.plugin_base import AbstractPlugin

__all__ = ["CyVoice"]


class CyVoice(AbstractPlugin):
    __TRANSLATE_PLUGIN_NAME: str = "BaiduTranslater"
    __TRANSLATE_METHOD_NAME: str = "translate"
    __TRANSLATE_METHOD_TYPE = Callable[[str, str, str], str]  # [tolang, query, fromlang] -> str

    __READ_CMD = "read"
    __CHANGE_CV_CMD = "change"
    __LIST_CV_CMD = "list"
    __CURRENT_CV_CMD = "current"
    __CONFIG_CMD = "config"
    __CONFIG_SET_CMD = "set"
    __CONFIG_LIST_CMD = "list"

    __TRANSLATE_CMD = "trans"
    __TRANSLATE_ENABLE_CMD = "enable"
    __TRANSLATE_TO_LANG_CMD = "target_lang"

    CONFIG_NOISE = "Noise"
    CONFIG_NOISE_W = "NoiseW"
    CONFIG_MAX = "Max"
    CONFIG_ENABLE_TRANSLATE = "EnableTrans"
    CONFIG_TARGET_LANGUAGE = "TargetLang"

    CONFIG_ANNOTATE_STATEMENT = "AnnotateStatement"
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
        return "0.0.2"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "cv")
        self._config_registry.register_config(self.CONFIG_API_HOST_URL, "http://127.0.0.1:23456")
        self._config_registry.register_config(self.CONFIG_USED_CV_INDEX, 0)
        self._config_registry.register_config(self.CONFIG_TEMP_FILE_DIR_PATH, f"{self._get_config_parent_dir()}/temp")

        self._config_registry.register_config(self.CONFIG_NOISE, 0.667)
        self._config_registry.register_config(self.CONFIG_NOISE_W, 0.8)
        self._config_registry.register_config(self.CONFIG_MAX, 50)

        self._config_registry.register_config(self.CONFIG_ENABLE_TRANSLATE, 1)
        self._config_registry.register_config(self.CONFIG_TARGET_LANGUAGE, "jp")

        self._config_registry.register_config(self.CONFIG_ANNOTATE_STATEMENT, "ちゃんと聞いてくださいね、私の名前は")

    def install(self):
        from graia.ariadne.message.element import Voice
        from modules.cmd import CmdBuilder
        from .api import VITS

        self.__register_all_config()
        self._config_registry.load_config()
        translater: Optional[AbstractPlugin] = self._plugin_view.get(self.__TRANSLATE_PLUGIN_NAME, None)
        if translater:
            translate: CyVoice.__TRANSLATE_METHOD_TYPE = getattr(translater, self.__TRANSLATE_METHOD_NAME)

        temp_dir: str = self._config_registry.get_config(self.CONFIG_TEMP_FILE_DIR_PATH)
        os.makedirs(temp_dir, exist_ok=True)
        VITS.base = self._config_registry.get_config(self.CONFIG_API_HOST_URL)
        cmd_builder = CmdBuilder(
            config_setter=self._config_registry.set_config, config_getter=self._config_registry.get_config
        )
        configurable_options: List[str] = [
            self.CONFIG_NOISE,
            self.CONFIG_NOISE_W,
            self.CONFIG_MAX,
            self.CONFIG_ENABLE_TRANSLATE,
            self.CONFIG_TARGET_LANGUAGE,
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

        def change_cv_index(index: int) -> str:
            temp = self._config_registry.get_config(self.CONFIG_USED_CV_INDEX)
            self._config_registry.set_config(self.CONFIG_USED_CV_INDEX, index)
            return f"change cv index [{temp}] to [{index}]"

        def get_current_cv() -> Voice:
            cv_id: int = self._config_registry.get_config(self.CONFIG_USED_CV_INDEX)
            speaker_names = VITS.get_voice_speakers()
            return Voice(
                path=VITS.voice_vits(
                    f"{self._config_registry.get_config(self.CONFIG_ANNOTATE_STATEMENT)}{speaker_names[cv_id]}ですわ！",
                    id=cv_id,
                    save_dir=self._config_registry.get_config(self.CONFIG_TEMP_FILE_DIR_PATH),
                )
            )

        def read_sentence(sentence: str) -> Voice:
            if self._config_registry.get_config(self.CONFIG_ENABLE_TRANSLATE) and translate:
                save_path = VITS.voice_vits(
                    translate(self._config_registry.get_config(self.CONFIG_TARGET_LANGUAGE), sentence, "auto"),
                    id=self._config_registry.get_config(self.CONFIG_USED_CV_INDEX),
                    save_dir=temp_dir,
                )
            else:
                save_path = VITS.voice_vits(
                    sentence, id=self._config_registry.get_config(self.CONFIG_USED_CV_INDEX), save_dir=temp_dir
                )
            return Voice(path=save_path)

        def list_out_speakers() -> str:
            speaker_names = VITS.get_voice_speakers()
            temp_string = ""
            if translate:
                for index, name in enumerate(speaker_names):
                    temp_string += f" ID: {index:<4}|{name:<8}|{translate('zh',name,'auto')}\n"
            else:
                for index, name in enumerate(speaker_names):
                    temp_string += f" ID: {index:<4}|{name:<8}\n"
            return temp_string

        tree = {
            self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD): {
                self.__LIST_CV_CMD: list_out_speakers,
                self.__CHANGE_CV_CMD: change_cv_index,
                self.__READ_CMD: read_sentence,
                self.__CURRENT_CV_CMD: get_current_cv,
                self.__CONFIG_CMD: {
                    self.__CONFIG_LIST_CMD: list_out_configs,
                    self.__CONFIG_SET_CMD: cmd_builder.build_setter_hall(),
                },
                self.__TRANSLATE_CMD: {
                    self.__TRANSLATE_ENABLE_CMD: cmd_builder.build_setter_for(self.CONFIG_ENABLE_TRANSLATE),
                    self.__TRANSLATE_TO_LANG_CMD: cmd_builder.build_setter_for(self.CONFIG_TARGET_LANGUAGE),
                },
            }
        }
        self._cmd_client.register(tree, True)
