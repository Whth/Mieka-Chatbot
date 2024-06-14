import re
from typing import Dict, Union

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Forward

from modules.file_manager import download_file
from modules.shared import (
    AbstractPlugin,
    EnumCMD,
    get_pwd,
    NameSpaceNode,
    ExecutableNode,
    assemble_cmd_regex_parts,
    make_regex_part_from_enum,
)
from .extractor import extract_images_from_forward


class CMD(EnumCMD):
    extractor = ["ecx", "ect"]
    recurxport = ["p", "xrt"]


class PicExtractor(AbstractPlugin):
    CONFIG_CACHE_DIR = "cache_dir"

    DefaultConfig: Dict = {CONFIG_CACHE_DIR: f"{get_pwd()}/cache"}

    @classmethod
    def get_plugin_name(cls) -> str:
        return "PicExtractor"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "extract images from the nested forward message"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "None"

    def install(self):
        tree = NameSpaceNode(
            **CMD.extractor.export(),
            help_message=self.get_plugin_description(),
            required_permissions=self.required_permission,
            children_node=[ExecutableNode(**CMD.recurxport.export(), source=lambda *x: None)],
        )
        self.root_namespace_node.add_node(tree)

        @self.receiver(
            event=[GroupMessage, FriendMessage],
        )
        async def extract(app: Ariadne, msg_event: GroupMessage | FriendMessage):
            """
            Extract images from the nested forward
            Args:
                app:
                msg_event:

            Returns:


            """
            parts = assemble_cmd_regex_parts(
                [make_regex_part_from_enum(CMD.extractor), make_regex_part_from_enum(CMD.recurxport), ".*"]
            )
            pat = re.compile(parts)
            if not pat.findall(str(msg_event.message_chain)):
                return

            quoted_msg_event = await app.get_message_from_id(msg_event.quote.id)
            if not isinstance(quoted_msg_event, Union[GroupMessage | FriendMessage]):
                return

            quoted_msg: MessageChain = quoted_msg_event.message_chain

            if not quoted_msg.has(Forward):
                return

            images = await extract_images_from_forward(quoted_msg.get(Forward)[0])
            images_fp = await download_file(
                [img.url for img in images], save_dir=self.config_registry.get_config(self.CONFIG_CACHE_DIR)
            )
            await app.send_message(msg_event, f"Extracted {len(images_fp)} images")
            await app.send_message(msg_event, images)
