from random import sample
from typing import Sequence

from graia.ariadne.message.element import Image

from modules.auth.core import required_perm_generator
from modules.auth.permissions import Permission, PermissionCode
from modules.cmd import NameSpaceNode, ExecutableNode, RequiredPermission
from modules.file_manager import explore_folder
from modules.file_manager import get_pwd
from modules.plugin_base import AbstractPlugin

__all__ = ["RandomMeme"]


class CMD:
    ROOT = "meme"
    GET_MEME = "c"


class RandomMeme(AbstractPlugin):
    GIF_ASSET_PATH = "gif_asset_path"

    DefaultConfig = {
        GIF_ASSET_PATH: f"{get_pwd()}/asset",
    }

    @classmethod
    def get_plugin_name(cls) -> str:
        return "RandomMeme"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "send random meme"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.2"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def install(self):
        su_perm = Permission(id=PermissionCode.SuperPermission.value, name=self.get_plugin_name())
        req_perm: RequiredPermission = required_perm_generator(
            target_resource_name=self.get_plugin_name(), super_permissions=[su_perm]
        )

        def get_memes(count: int = 1) -> Sequence:
            """
            Generate a sequence of Image objects representing memes.

            Args:
                count (int, optional): The number of memes to generate.
                        Default to 1.

            Returns:
                Sequence: A sequence of Image objects representing memes.
            """
            paths = explore_folder(self.config_registry.get_config(self.GIF_ASSET_PATH))
            if len(paths) == 0:
                raise FileNotFoundError(f"no gif found in {self.config_registry.get_config(self.GIF_ASSET_PATH)}")
            count = len(paths) if len(paths) < count else count
            cut_paths = sample(paths, count)

            return [Image(path=path) for path in cut_paths]

        tree = NameSpaceNode(
            name=CMD.ROOT,
            help_message=self.get_plugin_description(),
            required_permissions=req_perm,
            children_node=[ExecutableNode(name=CMD.GET_MEME, help_message=get_memes.__doc__, source=get_memes)],
        )
        self._auth_manager.add_perm_from_req(req_perm)
        self._root_namespace_node.add_node(tree)
