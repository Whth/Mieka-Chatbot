import os
from random import choice

from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.base import ContainKeyword
from graia.ariadne.model import Group

from modules.plugin_base import AbstractPlugin

__all__ = ["Magi"]


class Magi(AbstractPlugin):
    CONFIG_GIF_ASSET_PATH: str = "gif_asset_path"
    CONFIG_DETECTED_KEYWORD: str = "detected_keyword"
    CONFIG_TEMP_DIR_PATH: str = "temp_dir_path"

    CONFIG_PASS_FRAME_COUNT: str = "pass_frame_count"
    CONFIG_EVAL_GIF_LOOP_COUNT: str = "eval_gif_loop_count"
    CONFIG_RESULT_FRAME_DURATION: str = "result_frame_duration"

    __PASS_DIR_NAME: str = "pass"
    __EVALUATING_DIR_NAME: str = "evaluating"
    __EVALUATING_GIF_NAME: str = "result.gif"
    __TEMP_FILE_NAME: str = "eval_pass.gif"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "MAGI_SYS"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "generate random Magi decision-making gif"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_GIF_ASSET_PATH, f"{self._get_config_parent_dir()}/asset")
        self._config_registry.register_config(self.CONFIG_TEMP_DIR_PATH, f"{self._get_config_parent_dir()}/temp")
        self._config_registry.register_config(self.CONFIG_PASS_FRAME_COUNT, 20)
        self._config_registry.register_config(self.CONFIG_EVAL_GIF_LOOP_COUNT, 3)
        self._config_registry.register_config(self.CONFIG_RESULT_FRAME_DURATION, 80)
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "magi")

    def install(self):
        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast

        gif_dir_path: str = self._config_registry.get_config(self.CONFIG_GIF_ASSET_PATH)
        temp_dir_path: str = self._config_registry.get_config(self.CONFIG_TEMP_DIR_PATH)

        temp_file_path: str = f"{temp_dir_path}/{self.__TEMP_FILE_NAME}"
        eval_file_path: str = f"{gif_dir_path}/{self.__EVALUATING_DIR_NAME}/{self.__EVALUATING_GIF_NAME}"

        gif_count: int = self._config_registry.get_config(self.CONFIG_EVAL_GIF_LOOP_COUNT)
        jpg_count: int = self._config_registry.get_config(self.CONFIG_PASS_FRAME_COUNT)
        duration: int = self._config_registry.get_config(self.CONFIG_RESULT_FRAME_DURATION)
        from modules.file_manager import explore_folder
        from .gif_factory import GifFactory

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD))],
        )
        async def MAGI_SYS_DECISION_MAKING(group: Group):
            """
            random send a gif in a day
            :param group:
            :return:
            """
            random_pass_file_path = choice(explore_folder(f"{gif_dir_path}/{self.__PASS_DIR_NAME}"))
            GifFactory.append_jpg_to_gif(
                jpg_path=random_pass_file_path,
                jpg_count=jpg_count,
                gif_path=eval_file_path,
                gif_count=gif_count,
                output_path=temp_file_path,
                duration=duration,
            )
            await ariadne_app.send_message(group, Image(path=temp_file_path))
