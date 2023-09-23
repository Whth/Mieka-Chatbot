import os

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
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "recall")
        self._config_registry.register_config(self.CONFIG_MAX_LOOK_BACK, 10)

    def install(self):
        from graia.ariadne.event.message import GroupMessage
        from graia.ariadne.message.parser.base import ContainKeyword, MentionMe
        from graia.ariadne.model import Group
        from colorama import Fore

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast
        max_look_back: int = self._config_registry.get_config(self.CONFIG_MAX_LOOK_BACK)

        @bord_cast.receiver(
            GroupMessage,
            decorators=[
                MentionMe(),
                ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD)),
            ],
        )
        async def recall_handler(group: Group, message_event: GroupMessage):
            """
            Handle the recall action for a group message event.

            Args:
                group (Group): The group where the recall action is triggered.
                message_event (GroupMessage): The group message event triggering the recall action.
            """
            this_message_id = message_event.id

            # Check if the message event has a quote
            if not hasattr(message_event.quote, "origin"):
                print(f"{Fore.RED}No Quote")
                print(f"{Fore.RED}Searching previous [{max_look_back}] messages{Fore.RESET}")

                # Search for the previous messages in the group
                for i in range(1, max_look_back + 1):
                    temp: GroupMessage = await ariadne_app.get_message_from_id(this_message_id - i, group)

                    # Check if the previous message is sent by the same account
                    if temp.sender.id == ariadne_app.account:
                        message_to_recall = temp
                        print(f"{Fore.RED}Found Message-{temp.id}{Fore.RESET}")
                        break
                else:
                    print(f"{Fore.RED}No message Found, Not execute recall action{Fore.RESET}")
                    return

            else:
                # Get the message to recall from the quote
                message_to_recall: GroupMessage = await ariadne_app.get_message_from_id(message_event.quote.id, group)

            # Check if the message to recall is not sent by the same account
            if message_to_recall.sender.id != ariadne_app.account:
                print(
                    f"{Fore.RED}Quote message is from {message_to_recall.sender.id}, not {ariadne_app.account}\n"
                    f"Not execute recall action.{Fore.RED}"
                )

            print(f"{Fore.GREEN}Recall Message-{message_to_recall.id} in Group-{group.id}{Fore.RESET}")

            # Recall the message
            await ariadne_app.recall_message(message_to_recall, group)
