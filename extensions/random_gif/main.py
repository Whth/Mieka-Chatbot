import os
import random

from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.base import ContainKeyword
from graia.ariadne.model import Group

from modules.plugin_base import AbstractPlugin

__all__ = ["RandomMeme"]


class RandomMeme(AbstractPlugin):
    GIF_ASSET_PATH = "gif_asset_path"
    DETECTED_KEYWORD = "detected_keyword"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "RandomMeme"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "send random meme"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.GIF_ASSET_PATH, f"{self._get_config_parent_dir()}/asset")
        self._config_registry.register_config(self.DETECTED_KEYWORD, "meme")

    def install(self):
        self.__register_all_config()
        self._config_registry.load_config()
        from modules.file_manager import explore_folder

        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast

        gif_dir_path = self._config_registry.get_config(self.GIF_ASSET_PATH)

        @bord_cast.receiver(
            "GroupMessage", decorators=[ContainKeyword(keyword=self._config_registry.get_config(self.DETECTED_KEYWORD))]
        )
        async def random_emoji(group: Group):
            """
            random send a gif in a day
            :param group:
            :return:
            """

            await ariadne_app.send_message(group, Image(path=random.choice(explore_folder(gif_dir_path))))