import os
import random

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
        from modules.file_manager import explore_folder
        from graia.ariadne.message.element import Image
        from graia.ariadne.message.parser.base import ContainKeyword
        from graia.ariadne.model import Group
        from graia.ariadne.event.message import GroupMessage

        self.__register_all_config()
        self._config_registry.load_config()

        gif_dir_path = self._config_registry.get_config(self.GIF_ASSET_PATH)

        from graia.ariadne import Ariadne

        @self.receiver(
            GroupMessage,
            decorators=[ContainKeyword(keyword=self._config_registry.get_config(self.DETECTED_KEYWORD))],
        )
        async def random_emoji(app: Ariadne, group: Group):
            """
            random send a gif in a day
            :param group:
            :return:
            """

            await app.send_message(group, Image(path=random.choice(explore_folder(gif_dir_path))))
