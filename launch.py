from typing import List

from graia.ariadne.connection.config import WebsocketClientConfig

from constant import CONFIG_FILE_NAME, CONFIG_DIR, EXTENSION_DIR
from modules.chat_bot import ChatBot, BotInfo, BotConfig, BotConnectionConfig
from modules.config_utils import ConfigRegistry, CmdClient

WEBSOCKET_HOST = "websocket_host"

VERIFY_KEY = "verify_key"

ACCOUNT_ID = "account_id"
ACCEPTED_MESSAGE_TYPES = "accepted_message_types"
__version__ = "v0.3.1"


def make_help_cmd(client: CmdClient):
    def _cmds():
        temp_string = "Available CMD:\n"
        for cmd in client.get_all_available_cmd:
            temp_string += f"\t{cmd}\n"
        return temp_string

    return _cmds


def make_installed_plugins_cmd(plugins_view):
    def _plugins():
        return "\n".join(
            f"{plugin.get_plugin_name()}==>V{plugin.get_plugin_version():>}" for plugin in plugins_view.values()
        )

    return _plugins


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
                "version": lambda: __version__,
                "areas": lambda: "\n".join(Mieka.accepted_message_types),  # FIXME unsafe exposure
            },
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

    updated_tree = {
        "bot": {
            "cmds": make_help_cmd(__bot.client),
            "extensions": make_installed_plugins_cmd(__bot.get_installed_plugins),
        }
    }

    __bot.client.register(updated_tree, True)

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
