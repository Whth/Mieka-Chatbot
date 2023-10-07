import os
import pathlib

from modules.plugin_base import AbstractPlugin

__all__ = ["Novelin"]


class Novelin(AbstractPlugin):
    CONFIG_NOVEL_ASSET_PATH = "novel_asset_path"
    CONFIG_DETECTED_KEYWORD = "detected_keyword"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "Novelin"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "sends random sampled string, like novel"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_NOVEL_ASSET_PATH, f"{self._get_config_parent_dir()}/asset")
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "nvlin")

    def install(self):
        from .extractor import get_paragraph, remove_blank_lines
        from modules.file_manager import explore_folder
        from random import choice

        self.__register_all_config()
        self._config_registry.load_config()

        asset_path = self._config_registry.get_config(self.CONFIG_NOVEL_ASSET_PATH)
        pathlib.Path(asset_path).mkdir(parents=True, exist_ok=True)

        def _some_novel(length: int) -> str:
            path = choice(explore_folder(asset_path))
            remove_blank_lines(path)
            return get_paragraph(path, length)

        tree = {self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD): _some_novel}
        self._root_namespace_node.register(tree, True)
