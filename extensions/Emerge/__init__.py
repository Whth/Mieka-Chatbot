from graia.ariadne.event.lifecycle import ApplicationLaunch

from modules.file_manager import get_pwd
from modules.plugin_base import AbstractPlugin
from modules.shared import EnumCMD

__all__ = ["Emerge"]
class CMD(EnumCMD):
    emojimerge = ["eme","emerge"]

class Emerge(AbstractPlugin):
    CONFIG_CACHE_DIR_PATH = "cache_dir_path"
    CONFIG_DB_FILE_PATH = "db_file_path"
    DefaultConfig = {CONFIG_CACHE_DIR_PATH: f"{get_pwd()}/cache",
                     CONFIG_DB_FILE_PATH: f"{get_pwd()}/data_base.json"}



    @classmethod
    def get_plugin_name(cls) -> str:
        return "Emerge"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "emoji merge plugin"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.2"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def install(self):
        from graia.ariadne.message.element import Image
        from colorama import Back
        from modules.cmd import RequiredPermission, ExecutableNode
        from modules.auth.resources import required_perm_generator
        from modules.auth.permissions import Permission, PermissionCode
        from .api import EmojiMerge

        cache_dir = self._config_registry.get_config(self.CONFIG_CACHE_DIR_PATH)
        data_file= self._config_registry.get_config(self.CONFIG_DB_FILE_PATH)
        merger = EmojiMerge(cache_dir,data_file)


        @self.receiver(ApplicationLaunch)
        async def init_merger():
            await merger.init_data_base()

        def _merge_emoji(emoji_1: str, emoji_2: str) -> Image | str:
            """
            Merge two emojis and return the merged result as an Image object or a string.

            Args:
                emoji_1 (str): The first emoji to be merged.
                emoji_2 (str): The second emoji to be merged.

            Returns:
                Image or str: The merged emoji as an Image object if successful, or a string indicating failure.
            """
            print(f"{Back.YELLOW}Merge {emoji_1} and {emoji_2}{Back.RESET}")
            path = merger.merge(emoji_1, emoji_2)
            if path is None:
                from random import choice

                return choice(["合不了哟~", "抽象", "不行", "不可以哟~",])
            return Image(path=path)

        su_perm = Permission(id=PermissionCode.SuperPermission.value, name=self.get_plugin_name())
        req_perm: RequiredPermission = required_perm_generator(
            target_resource_name=self.get_plugin_name(), super_permissions=[su_perm]
        )
        tree = ExecutableNode(
            **CMD.emojimerge.export(), source=_merge_emoji, required_permissions=req_perm, help_message=_merge_emoji.__doc__
        )
        self._auth_manager.add_perm_from_req(req_perm)
        self._root_namespace_node.add_node(tree)
