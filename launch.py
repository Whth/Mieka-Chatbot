from typing import List

from graia.ariadne.connection.config import WebsocketClientConfig

from constant import CONFIG_FILE_NAME, CONFIG_DIR, EXTENSION_DIR
from modules.chat_bot import ChatBot, BotInfo, BotConfig, BotConnectionConfig
from modules.config_utils import ConfigRegistry, ConfigClient
from modules.file_manager import get_all_sub_dirs

WEBSOCKET_HOST = "websocket_host"

VERIFY_KEY = "verify_key"

ACCOUNT_ID = "account_id"
ACCEPTED_MESSAGE_TYPES = "accepted_message_types"
__version__ = "v0.3.1"


def get_all_cmd_info() -> str:
    temp_string = "Available CMD:\n"
    for cmd in ConfigClient.get_all_available_cmd():
        temp_string += f"\t{cmd}\n"
    return temp_string


class Mieka(object):
    """
    Mieka chatbot
    """

    __NAME = "Mieka"
    __config = ConfigRegistry(f"{CONFIG_DIR}/{__NAME}_{CONFIG_FILE_NAME}")
    __config.register_config(ACCOUNT_ID, 1234567890)
    __config.register_config(VERIFY_KEY, "INITKEYXBVCdNG0")

    __config.register_config(WEBSOCKET_HOST, "http://127.0.0.1:8080")
    __config.register_config(ACCEPTED_MESSAGE_TYPES, ["GroupMessage"])
    __config.load_config()
    accepted_message_types: List[str] = __config.get_config(ACCEPTED_MESSAGE_TYPES)
    __bot_info = BotInfo(account_id=__config.get_config(ACCOUNT_ID), bot_name=__NAME)
    __bot_config = BotConfig(
        extension_dir=EXTENSION_DIR,
        syntax_tree={
            "bot": {
                "cmds": get_all_cmd_info,
                "version": lambda: __version__,
                "extensions": lambda: "\n".join(get_all_sub_dirs(EXTENSION_DIR)),
                "areas": lambda: "\n".join(Mieka.accepted_message_types),  # FIXME unsafe exposure
            }
        },
        accepted_message_types=accepted_message_types,
    )
    __bot_connection_config = BotConnectionConfig(
        verify_key=__config.get_config(VERIFY_KEY),
        websocket_config=WebsocketClientConfig(host=__config.get_config(WEBSOCKET_HOST)),
    )
    __bot = ChatBot(
        bot_info=__bot_info,
        bot_config=__bot_config,
        bot_connection_config=__bot_connection_config,
    )

    @classmethod
    def run(cls):
        """
        run the bot, save config on exit
        Returns:

        """
        cls.__bot.run()
        cls.__config.save_all_configs()


if __name__ == "__main__":
    bot = Mieka()
    bot.run()
