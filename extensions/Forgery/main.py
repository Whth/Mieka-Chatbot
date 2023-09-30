import os
from typing import List, Tuple

from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.element import Plain, Forward, MultimediaElement

from modules.plugin_base import AbstractPlugin

__all__ = ["Forgery"]


class CMD:
    ROOT: str = "fake"


class Forgery(AbstractPlugin):
    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "Forgery"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "Fake history message"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        pass

    def install(self):
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.model import Group
        import re
        from .fake_chain import make_forward, get_messages

        self.__register_all_config()
        self._config_registry.load_config()

        reg = re.compile(rf"{CMD.ROOT}\s+(\d+)")

        extract_reg = re.compile(r"(\d+)(?:(\s+.+)?|$)")

        def extract_info(plain_txt: str) -> Tuple[int, str] | None:
            matched = re.match(extract_reg, string=plain_txt)
            if matched:
                # account id and plain string that will be sent
                matched_groups = matched.groups()
                return int(matched_groups[0]), matched_groups[1] if matched_groups[1] else ""
            return None

        from graia.ariadne import Ariadne

        async def fake(app: Ariadne, group: Group, message_event: GroupMessage):
            """
            random send a gif in a day
            :param group:
            :return:
            """
            matched = re.match(reg, string=str(message_event.message_chain))
            if not matched:
                return

            this_message_id: int = message_event.id
            batch_size = int(matched.groups()[0])

            retrieved_messages: List[GroupMessage] = await get_messages(app, group, batch_size, this_message_id - 1)

            info_pack = []
            for message in retrieved_messages:
                extracted_data = extract_info(str(message.message_chain.get(Plain, 1)[0]))
                if extracted_data is None:
                    raise RuntimeError("bad input chain")

                extract_multimedia_data = message.message_chain.get(MultimediaElement)

                info_pack.insert(
                    0, (extracted_data[0], MessageChain([Plain(extracted_data[1])] + extract_multimedia_data))
                )

            nodes = await make_forward(app, info_pack)

            await app.send_group_message(group, Forward(nodes))

        self.receiver(fake, GroupMessage)
