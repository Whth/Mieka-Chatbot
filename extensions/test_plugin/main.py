import os
import random

from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.base import ContainKeyword
from graia.ariadne.model import Group

from modules.plugin_base import AbstractPlugin

__all__ = ["TestPlugin"]


class TestPlugin(AbstractPlugin):
    CONFIG_GIF_ASSET_PATH = "gif_asset_path"
    CONFIG_DETECTED_KEYWORD = "detected_keyword"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "test"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "test plugin"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_GIF_ASSET_PATH, f"{self._get_config_parent_dir()}/asset")
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "mk")

    def install(self):
        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast

        gif_dir_path = self._config_registry.get_config(self.CONFIG_GIF_ASSET_PATH)

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD))],
        )
        async def random_emoji(group: Group):
            """
            random send a gif in a day
            :param group:
            :return:
            """

            await ariadne_app.send_message(group, Image(path=get_random_file(gif_dir_path)))


def get_random_file(folder):
    """

    :param folder:
    :return:
    """
    from modules.file_manager import explore_folder

    files_list = explore_folder(folder)
    return random.choice(files_list)
