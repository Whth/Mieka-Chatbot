from typing import List

from modules.file_manager import get_pwd
from modules.plugin_base import AbstractPlugin

__all__ = ["BegForMercy"]


class CMD:
    ROOT: str = "bfm"
    ADD: str = "add"
    LIST: str = "list"
    DEL: str = "del"


class BegForMercy(AbstractPlugin):
    CONFIG_BEGGING_GIF_ASSET_PATH = "gif_asset_path"
    CONFIG_DETECTED_KEYWORD_LIST = "detected_keyword_list"

    DefaultConfig = {
        CONFIG_BEGGING_GIF_ASSET_PATH: f"{get_pwd()}/asset",
        CONFIG_DETECTED_KEYWORD_LIST: ["sb"],
    }

    @classmethod
    def get_plugin_name(cls) -> str:
        return "BegForMercy"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "plugin that allow the bot react to the detected blaming, by sending gif or words"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.2"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def install(self):
        from random import choice
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.message.element import Image
        from graia.ariadne.message.parser.base import MentionMe
        from graia.ariadne.event.message import GroupMessage
        from graia.ariadne.model import Group
        from colorama import Back

        from modules.shared import explore_folder, ExecutableNode, NameSpaceNode, make_stdout_seq_string
        from graia.ariadne import Ariadne

        gif_dir_path = self._config_registry.get_config(self.CONFIG_BEGGING_GIF_ASSET_PATH)

        def _add_new_keyword(new_kw: str) -> str:
            """
            Adds a new keyword to the keyword list.

            Parameters:
                new_kw (str): The new keyword to be added.

            Returns:
                str: A message indicating the addition of the keyword and the current size of the keyword list.
            """
            kw_list: List[str] = self.config_registry.get_config(self.CONFIG_DETECTED_KEYWORD_LIST)
            kw_list.append(new_kw)
            kw_list = list(set(kw_list))
            self.config_registry.set_config(self.CONFIG_DETECTED_KEYWORD_LIST, kw_list)
            return f"add [{new_kw}], now kw_list sizes {len(kw_list)}"

        def _delete_keyword(new_kw: str) -> str:
            """
            Delete a keyword from the keyword list.

            Parameters:
                new_kw (str): The keyword to be deleted.

            Returns:
                str: A string indicating the result of the deletion operation.
            """
            kw_list: List[str] = self.config_registry.get_config(self.CONFIG_DETECTED_KEYWORD_LIST)
            kw_list.remove(new_kw)
            kw_list = list(set(kw_list))
            self.config_registry.set_config(self.CONFIG_DETECTED_KEYWORD_LIST, kw_list)
            return f"delete [{new_kw}], now kw_list sizes {len(kw_list)}"

        def _list_kws() -> str:
            """
            Get a list of detected keywords.

            Returns:
                str: A string representation of the detected keyword list.
            """
            kw_list: List[str] = self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD_LIST)

            return make_stdout_seq_string(kw_list)

        tree = NameSpaceNode(
            name=CMD.ROOT,
            required_permissions=self.required_permission,
            children_node=[
                ExecutableNode(
                    name=CMD.ADD,
                    required_permissions=self.required_permission,
                    source=_add_new_keyword,
                    help_message=_add_new_keyword.__doc__,
                ),
                ExecutableNode(
                    name=CMD.LIST,
                    required_permissions=self.required_permission,
                    source=_list_kws,
                    help_message=_list_kws.__doc__,
                ),
                ExecutableNode(
                    name=CMD.DEL,
                    required_permissions=self.required_permission,
                    source=_delete_keyword,
                    help_message=_delete_keyword.__doc__,
                ),
            ],
        )

        self._root_namespace_node.add_node(tree)

        @self.receiver(event=GroupMessage, decorators=[MentionMe()])
        async def begging_for_mercy(app: Ariadne, group: Group, message: MessageChain):
            """
            Decorator for a function that handles a GroupMessage event when the bot is mentioned.

            Args:
                app (Ariadne): The Ariadne instance.
                group (Group): The group where the message was sent.
                message (MessageChain): The message chain of the received message.

            Returns:
                None

            Raises:
                None
            """
            string = str(message)
            if all(
                keyword not in string for keyword in self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD_LIST)
            ):
                return
            file = choice(explore_folder(gif_dir_path))
            print(f"{Back.BLUE}BEG_FOR_MERCY: Sending file at [{file}]{Back.RESET}")
            await app.send_message(group, Image(path=file))
