import os

from modules.plugin_base import AbstractPlugin

__all__ = ["Emerge"]


class Emerge(AbstractPlugin):
    CONFIG_CACHE_DIR_PATH = "cache_dir_path"

    class CMD:
        ROOT = "eme"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "Emerge"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "emoji merge plugin"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_CACHE_DIR_PATH, f"{self._get_config_parent_dir()}/cache")

    def install(self):
        from graia.ariadne.message.element import Image
        from colorama import Back
        from .api import EmojiMerge

        self.__register_all_config()
        self._config_registry.load_config()

        cache_dir = self._config_registry.get_config(self.CONFIG_CACHE_DIR_PATH)
        merger = EmojiMerge(cache_dir)

        def _merge_emoji(emoji_1: str, emoji_2: str) -> Image | str:
            print(f"{Back.YELLOW}Merge {emoji_1} and {emoji_2}{Back.RESET}")
            path = merger.merge(emoji_1, emoji_2)
            if path is None:
                from random import choice

                return choice(["合不了", "抽象", "不行", "不可以"])
            return Image(path=path)

        tree = {self.CMD.ROOT: _merge_emoji}
        self._root_namespace_node.register(tree, True)
