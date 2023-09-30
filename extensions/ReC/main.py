import os
from typing import List, Optional, Sequence

from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.model import Group

from modules.plugin_base import AbstractPlugin

__all__ = ["ReC"]


class ReC(AbstractPlugin):
    CONFIG_DETECTED_KEYWORD = "detected_keyword"
    CONFIG_MAX_LOOK_BACK = "MaxLookBack"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "ReC"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "allow bot to recall the message on specified cmds"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.2"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "recall")
        self._config_registry.register_config(self.CONFIG_MAX_LOOK_BACK, 30)

    def install(self):
        from graia.ariadne.event.message import GroupMessage
        from graia.ariadne.message.parser.base import ContainKeyword, MentionMe
        from graia.ariadne.model import Group
        from colorama import Fore
        from graia.ariadne.exception import UnknownTarget

        self.__register_all_config()
        self._config_registry.load_config()
        max_look_back: int = self._config_registry.get_config(self.CONFIG_MAX_LOOK_BACK)

        async def recall_handler(app: Ariadne, group: Group, message_event: GroupMessage):
            """
            Handle the recall action for a group message event.

            Args:
                group (Group): The group where the recall action is triggered.
                message_event (GroupMessage): The group message event triggering the recall action.
            """
            last_message_id = message_event.id - 1
            print(last_message_id)
            messages_to_recall: List[GroupMessage] = []
            if hasattr(message_event.quote, "origin"):
                # Get the message to recall from the quote
                messages_to_recall.append(await app.get_message_from_id(message_event.quote.id, group))

            # Check if the message event has a quote
            else:
                print(f"{Fore.RED}No Quote")
                print(f"{Fore.RED}Searching previous [{max_look_back}] messages{Fore.RESET}")

                messages_to_recall.extend(
                    await search_messages(
                        app=app,
                        last_message_id=last_message_id,
                        look_back=max_look_back,
                        target_group=group,
                        target_member_id=[app.account],
                    )
                )

            print(f"{Fore.RED}Execute recall on {len(messages_to_recall)} messages{Fore.RESET}")
            # Recall the message
            await recall_group_messages(app, messages_to_recall, group)

        self.receiver(
            recall_handler,
            GroupMessage,
            decorators=[
                MentionMe(),
                ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD)),
            ],
        )

        async def search_messages(
            app: Ariadne,
            last_message_id: int,
            look_back: int,
            target_group: Group,
            target_member_id: Optional[Sequence[int]],
        ) -> List[GroupMessage]:
            """
            Search for previous messages in a group based on the last message ID, a look back interval, the target group, and optional target member IDs.

            Parameters:
                last_message_id (int): The ID of the last message from which to start searching.
                look_back (int): The number of messages to look back from the last message ID.
                target_group (Group): The target group in which to search for messages.
                target_member_id (Optional[Sequence[int]]): Optional member IDs to filter the search. If None, all messages will be considered.

            Returns:
                List[GroupMessage]: A list of GroupMessage objects representing the found messages.

            """
            messages_to_recall: List[GroupMessage] = []
            # Search for the previous messages in the group
            for i in range(last_message_id, last_message_id - look_back, -1):
                try:
                    temp: GroupMessage = await app.get_message_from_id(i, target_group)
                except UnknownTarget:
                    continue
                # Check if the previous message is sent by the same account
                if target_member_id is None or temp.sender.id in target_member_id:
                    messages_to_recall.append(temp)
                    print(f"{Fore.RED}Found Message-{temp.id}\n{temp.message_chain}{Fore.RESET}")
            return messages_to_recall


async def recall_group_messages(app: Ariadne, message: List[GroupMessage], group: Group):
    """
    Asynchronously recalls a list of group messages using the given Ariadne app.

    Args:
        app (Ariadne): The Ariadne app instance.
        message (List[GroupMessage]): A list of group messages to be recalled.
        group (Group): The group to which the messages belong.

    Returns:
        None
    """
    from graia.ariadne.exception import RemoteException

    for msg in message:
        try:
            await app.recall_message(msg, group)
        except RemoteException:
            continue
