import os
from typing import List, Callable, Optional

from modules.file_manager import get_pwd
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
    CONFIG_LENGTH = "Length"
    CONFIG_TARGET_LANGUAGE = "TargetLang"

    CONFIG_ANNOTATE_STATEMENT = "AnnotateStatement"
    CONFIG_DETECTED_KEYWORD = "Keyword"
    CONFIG_USED_CV_INDEX = "UsedCVIndex"
    CONFIG_API_HOST_URL = "ApiHostUrl"
    CONFIG_TEMP_FILE_DIR_PATH = "TempFileDirPath"

    DefaultConfig = {
        CONFIG_NOISE: 0.667,
        CONFIG_NOISE_W: 0.8,
        CONFIG_MAX: 448,
        CONFIG_ENABLE_TRANSLATE: 1,
        CONFIG_LENGTH: 1.0,
        CONFIG_TARGET_LANGUAGE: "jp",
        CONFIG_ANNOTATE_STATEMENT: "ちゃんと聞いてくださいね、私の名前は",
        CONFIG_DETECTED_KEYWORD: "cv",
        CONFIG_USED_CV_INDEX: 0,
        CONFIG_API_HOST_URL: "http://127.0.0.1:23456",
        CONFIG_TEMP_FILE_DIR_PATH: f"{get_pwd()}/temp",
    }

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

    def install(self):
        from graia.ariadne.message.element import Voice
        from modules.cmd import CmdBuilder
        from modules.cmd import NameSpaceNode, ExecutableNode
        from .api import VITS

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
            self.CONFIG_LENGTH,
            self.CONFIG_TARGET_LANGUAGE,
        ]

        def list_out_configs() -> str:
            """
            Generate a string representation of the configurations.

            Returns:
                str: The string representation of the configurations.
            """
            result_string = ""
            for option in configurable_options:
                result_string += f"{option} = {self._config_registry.get_config(option)}\n"
            return result_string

        def change_cv_index(index: int) -> str:
            """
            Change the current CV index to the specified index.

            Parameters:
                index (int): The index to set as the new CV index.

            Returns:
                str: A message indicating the change in CV index, including the previous and new values.
            """
            temp = self._config_registry.get_config(self.CONFIG_USED_CV_INDEX)
            self._config_registry.set_config(self.CONFIG_USED_CV_INDEX, index)
            return f"change cv index [{temp}] to [{index}]"

        async def get_current_cv() -> Voice:
            """
            Retrieves the current voice (cv) used for text-to-speech conversion.

            Returns:
                Voice: The voice object representing the current cv voice.
            """
            cv_id: int = self._config_registry.get_config(self.CONFIG_USED_CV_INDEX)
            speaker_names = await VITS.get_voice_speakers()
            return Voice(
                path=await VITS.voice_vits(
                    f"{self._config_registry.get_config(self.CONFIG_ANNOTATE_STATEMENT)}{speaker_names[cv_id]}ですわ！",
                    cv_id=cv_id,
                    save_dir=self._config_registry.get_config(self.CONFIG_TEMP_FILE_DIR_PATH),
                )
            )

        async def read_sentence(sentence: str) -> Voice:
            """
            Generates a voice using the given sentence.

            Args:
                sentence (str): The sentence to be used for generating the voice.

            Returns:
                Voice: The generated voice.

            Raises:
                None.
            """
            if self._config_registry.get_config(self.CONFIG_ENABLE_TRANSLATE) and translate:
                sentence = translate(self._config_registry.get_config(self.CONFIG_TARGET_LANGUAGE), sentence, "auto")

            save_path = await VITS.voice_vits(
                sentence,
                cv_id=self._config_registry.get_config(self.CONFIG_USED_CV_INDEX),
                noise_w=self._config_registry.get_config(self.CONFIG_NOISE_W),
                noise=self._config_registry.get_config(self.CONFIG_NOISE),
                length=self._config_registry.get_config(self.CONFIG_LENGTH),
                max_seg_length=self._config_registry.get_config(self.CONFIG_MAX),
                save_dir=temp_dir,
            )
            return Voice(path=save_path)

        async def list_out_speakers(page: int = 1, page_size: int = 100) -> str:
            """
            Generate a string containing the names of the speakers available in the VITS voice recognition system.

            Returns:
                str: A string containing the names of the speakers.

            """
            speaker_names: List[str] = await VITS.get_voice_speakers()
            speakers_count = len(speaker_names)
            all_pages = (speakers_count // page_size) + 1
            temp_string = f"Page ({page}/{all_pages})\n"
            start = (page - 1) * page_size
            end = page * page_size
            page_content = speaker_names[start : end if end < speakers_count else speakers_count]
            if self.config_registry.get_config(self.CONFIG_ENABLE_TRANSLATE) and translate:
                temp_string += f" ID |CV Name|Translated Name\n"
                for index, name in enumerate(page_content, start=page_size * (page - 1)):
                    temp_string += f" ID: {index:<4}|{name:<8}|{translate('zh', name, 'auto')}\n"
            else:
                for index, name in enumerate(page_content, start=page_size * (page - 1)):
                    temp_string += f" ID: {index:<4}|{name:<8}\n"
            return temp_string

        tree = NameSpaceNode(
            name=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD),
            required_permissions=self.required_permission,
            children_node=[
                ExecutableNode(
                    name=self.__LIST_CV_CMD,
                    source=list_out_speakers,
                    help_message=f"{list_out_configs.__doc__}",
                ),
                ExecutableNode(
                    name=self.__CHANGE_CV_CMD,
                    source=change_cv_index,
                    help_message=f"{change_cv_index.__doc__}",
                ),
                ExecutableNode(
                    name=self.__READ_CMD,
                    source=read_sentence,
                    help_message=f"{read_sentence.__doc__}",
                ),
                ExecutableNode(
                    name=self.__CURRENT_CV_CMD,
                    source=get_current_cv,
                    help_message=f"{get_current_cv.__doc__}",
                ),
                NameSpaceNode(
                    name=self.__CONFIG_CMD,
                    children_node=[
                        ExecutableNode(
                            name=self.__CONFIG_LIST_CMD,
                            source=list_out_configs,
                            help_message=f"{list_out_configs.__doc__}",
                        ),
                        ExecutableNode(
                            name=self.__CONFIG_SET_CMD,
                            source=cmd_builder.build_setter_hall(),
                        ),
                    ],
                ),
                NameSpaceNode(
                    name=self.__TRANSLATE_CMD,
                    children_node=[
                        ExecutableNode(
                            name=self.__TRANSLATE_ENABLE_CMD,
                            source=cmd_builder.build_setter_for(self.CONFIG_ENABLE_TRANSLATE),
                        ),
                        ExecutableNode(
                            name=self.__TRANSLATE_TO_LANG_CMD,
                            source=cmd_builder.build_setter_for(self.CONFIG_TARGET_LANGUAGE),
                        ),
                    ],
                ),
            ],
        )

        self._root_namespace_node.add_node(tree)
