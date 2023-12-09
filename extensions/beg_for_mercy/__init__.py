import pathlib
from random import choice
from typing import Set, Tuple

from colorama import Back
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.base import MentionMe
from graia.ariadne.model import Group

from modules.shared import (
    explore_folder,
    ExecutableNode,
    NameSpaceNode,
    make_stdout_seq_string,
    AbstractPlugin,
    get_pwd,
    generate_random_string,
)
from .rank import ProfanityRank, create_ranker_broad

__all__ = ["BegForMercy"]


class CMD:
    ROOT: str = "bfm"
    ADD: str = "add"
    LIST: str = "list"
    DEL: str = "del"
    RANK: str = "rank"


class BegForMercy(AbstractPlugin):
    CONFIG_BEGGING_GIF_ASSET_PATH = "gif_asset_path"
    CONFIG_DETECTED_KEYWORD_LIST = "detected_keyword_list"
    CONFIG_PF_RANK_PATH = "pf_rank_path"
    CONFIG_TEMP_DIR = "temp_dir"
    CONFIG_FONT_FILE = "font_file"

    DefaultConfig = {
        CONFIG_BEGGING_GIF_ASSET_PATH: f"{get_pwd()}/asset",
        CONFIG_PF_RANK_PATH: f"{get_pwd()}/rank.json",
        CONFIG_TEMP_DIR: f"{get_pwd()}/temp",
        CONFIG_FONT_FILE: f"{get_pwd()}/得意黑 TTF.ttf",
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
        gif_dir_path = self._config_registry.get_config(self.CONFIG_BEGGING_GIF_ASSET_PATH)
        pf_rank_path = pathlib.Path(self._config_registry.get_config(self.CONFIG_PF_RANK_PATH))
        if pf_rank_path.exists():
            pf_rank: ProfanityRank = ProfanityRank.parse_file(pf_rank_path)
        else:
            pf_rank = ProfanityRank()
            pf_rank.save(pf_rank_path)

        def _add_new_keyword(new_kw: str) -> str:
            """
            Adds a new keyword to the keyword list.

            Parameters:
                new_kw (str): The new keyword to be added.

            Returns:
                str: A message indicating the addition of the keyword and the current size of the keyword list.
            """
            kw_list: Set[str] = pf_rank.profanities
            kw_list.add(new_kw)
            pf_rank.save(pf_rank_path)
            return f"add [{new_kw}], now kw_list sizes {len(kw_list)}"

        def _delete_keyword(new_kw: str) -> str:
            """
            Delete a keyword from the keyword list.

            Parameters:
                new_kw (str): The keyword to be deleted.

            Returns:
                str: A string indicating the result of the deletion operation.
            """
            kw_list: Set[str] = pf_rank.profanities
            kw_list.remove(new_kw)
            pf_rank.save(pf_rank_path)
            return f"delete [{new_kw}], now kw_list sizes {len(kw_list)}"

        def _list_kws() -> str:
            """
            Get a list of detected keywords.

            Returns:
                str: A string representation of the detected keyword list.
            """
            kw_list: Set[str] = pf_rank.profanities

            return make_stdout_seq_string(kw_list)

        async def _get_rank(pure_txt: bool = False) -> str | Image:
            """
            Retrieves the rankers and returns either a string or an Image based on the value of `pure_txt`.

            Args:
                pure_txt (bool): A boolean value indicating whether the output should be in plain text format.

            Returns:
                str | Image: Either a string containing the rankers information or an Image object.
            """
            rankers = await pf_rank.get_rankers(app=Ariadne.current())
            if pure_txt:
                stdout = ""
                for i, ranker_data in enumerate(rankers.items(), start=1):
                    i: int
                    ranker_data: Tuple[Tuple[int, str], int]
                    ranker_info, ranker_score = ranker_data
                    stdout += f"[{i}] {ranker_info[0]}-{ranker_info[1]}\nNG-Word检测次数：{ranker_score}\n\n"

                return stdout
            else:
                temp_dir = self.config_registry.get_config(self.CONFIG_TEMP_DIR)
                font_file = self.config_registry.get_config(self.CONFIG_FONT_FILE)
                png_file = f"{temp_dir}/{generate_random_string(6)}.png"
                create_ranker_broad(
                    ranker_data=rankers,
                    save_path=png_file,
                    font_file=font_file,
                )
                return Image(path=png_file)

        tree = NameSpaceNode(
            name=CMD.ROOT,
            required_permissions=self.required_permission,
            children_node=[
                ExecutableNode(
                    name=CMD.ADD,
                    source=_add_new_keyword,
                    help_message=_add_new_keyword.__doc__,
                ),
                ExecutableNode(
                    name=CMD.LIST,
                    source=_list_kws,
                    help_message=_list_kws.__doc__,
                ),
                ExecutableNode(
                    name=CMD.DEL,
                    source=_delete_keyword,
                    help_message=_delete_keyword.__doc__,
                ),
                ExecutableNode(
                    name=CMD.RANK,
                    source=_get_rank,
                    help_message=_get_rank.__doc__,
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

        @self.receiver(event=GroupMessage)
        async def recording(msg_event: GroupMessage):
            """
            Decorator for a function that handles a GroupMessage event.

            Args:
                msg_event (GroupMessageEvent): The GroupMessageEvent instance.

            Returns:
                None

            Raises:
                None
            """
            if pf_rank.update_records(msg_event.sender.id, message=str(msg_event.message_chain)):
                pf_rank.save(pf_rank_path)
