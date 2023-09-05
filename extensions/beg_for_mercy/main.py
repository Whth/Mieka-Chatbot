import os

from modules.plugin_base import AbstractPlugin

__all__ = ["BegForMercy"]


class BegForMercy(AbstractPlugin):
    CONFIG_BEGGING_GIF_ASSET_PATH = "gif_asset_path"
    CONFIG_DETECTED_KEYWORD_LIST = "detected_keyword_list"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "BegForMercy"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "plugin that allow the bot react to the detected blaming, by sending gif or words"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(
            self.CONFIG_BEGGING_GIF_ASSET_PATH, f"{self._get_config_parent_dir()}/asset"
        )
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD_LIST, ["sb"])

    def install(self):
        from random import choice
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.message.element import Image
        from graia.ariadne.message.parser.base import MentionMe
        from graia.ariadne.model import Group
        from colorama import Back
        from modules.file_manager import explore_folder

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast

        gif_dir_path = self._config_registry.get_config(self.CONFIG_BEGGING_GIF_ASSET_PATH)

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[MentionMe()],
        )
        async def begging_for_mercy(group: Group, message: MessageChain):
            """
            A decorator that receives `GroupMessage` events and checks if they contain certain keywords.
            If the message contains any of the specified keywords, the `begging_for_mercy` function is triggered.
            The function takes two parameters: `group` and `message`. `group` is of type `Group` and represents
            the group in which the message was sent. `message` is of type `MessageChain` and represents the
            message that triggered the event.

            The function first converts the `message` object to a string. Then, it checks if none of the keywords
            specified in the configuration are present in the string. If none of the keywords are found, the
            function returns immediately.

            If at least one keyword is found in the message, the function proceeds to select a random file from
            the `gif_dir_path` folder using the `explore_folder` function. It then prints a debug message indicating
            the file that is being sent. Finally, it sends the selected file as an image to the group using the
            `ariadne_app.send_message` function.

            The function is asynchronous and therefore is decorated with the `async` keyword.

            Parameters:
            - `group` (Group): The group in which the message was sent.
            - `message` (MessageChain): The message that triggered the event.

            Returns:
            - None
            """
            string = str(message)
            if all(
                keyword not in string for keyword in self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD_LIST)
            ):
                return
            file = choice(explore_folder(gif_dir_path))
            print(f"{Back.BLUE}BEG_FOR_MERCY: Sending file at [{file}]{Back.RESET}")
            await ariadne_app.send_message(group, Image(path=file))
