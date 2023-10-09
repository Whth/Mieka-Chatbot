import pathlib
from enum import Enum
from graia.ariadne.connection.config import WebsocketClientConfig
from typing import List

from constant import CONFIG_FILE_NAME, CONFIG_DIR, EXTENSION_DIR
from modules.chat_bot import ChatBot, BotInfo, BotConfig, BotConnectionConfig
from modules.cmd import ExecutableNode, NameSpaceNode
from modules.config_utils import ConfigRegistry


class DefaultConfig(Enum):
    WEBSOCKET_HOST = "http://127.0.0.1:8080"
    AUTH_CONFIG_FILE_NAME: str = f"{CONFIG_DIR}/auth_manager.json"
    VERIFY_KEY = "INITKEYXBVCdNG0"
    ACCOUNT_ID = 1234567890
    ACCEPTED_MESSAGE_TYPES = ["GroupMessage"]
    VERSION = "v0.4.4"


def make_help_cmd(client: NameSpaceNode):
    def _cmds():
        return client.__doc__()

    return _cmds


def make_installed_plugins_cmd(plugins_view):
    def _plugins():
        return "\n".join(
            f"{plugin.get_plugin_name()}==>V{plugin.get_plugin_version():>}" for plugin in plugins_view.values()
        )

    return _plugins


class CMD:
    ROOT = "bot"
    VERSION = "version"
    PLUGINS = "plugins"
    HELP = "cmds"
    SU = "su"


class Mieka(object):
    """
    Mieka chatbot
    """

    __NAME = "Mieka"
    pathlib.Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    __config = ConfigRegistry(f"{CONFIG_DIR}/{__NAME}_{CONFIG_FILE_NAME}")
    __config.register_config(DefaultConfig.ACCOUNT_ID.name, DefaultConfig.ACCOUNT_ID.value)
    __config.register_config(DefaultConfig.VERIFY_KEY.name, DefaultConfig.VERIFY_KEY.value)
    __config.register_config(DefaultConfig.AUTH_CONFIG_FILE_NAME.name, DefaultConfig.AUTH_CONFIG_FILE_NAME.value)
    __config.register_config(DefaultConfig.WEBSOCKET_HOST.name, DefaultConfig.WEBSOCKET_HOST.value)
    __config.register_config(DefaultConfig.ACCEPTED_MESSAGE_TYPES.name, DefaultConfig.ACCEPTED_MESSAGE_TYPES.value)
    __config.load_config()
    accepted_message_types: List[str] = __config.get_config(DefaultConfig.ACCEPTED_MESSAGE_TYPES.name)
    __bot_info = BotInfo(account_id=__config.get_config(DefaultConfig.ACCOUNT_ID.name), bot_name=__NAME)
    __bot_config = BotConfig(
        extension_dir=EXTENSION_DIR,
        auth_config_file_path=__config.get_config(DefaultConfig.AUTH_CONFIG_FILE_NAME.name),
        accepted_message_types=accepted_message_types,
    )
    __bot_connection_config = BotConnectionConfig(
        verify_key=__config.get_config(DefaultConfig.VERIFY_KEY.name),
        websocket_config=WebsocketClientConfig(host=__config.get_config(DefaultConfig.WEBSOCKET_HOST.name)),
    )
    __bot = ChatBot(
        bot_info=__bot_info,
        bot_config=__bot_config,
        bot_connection_config=__bot_connection_config,
    )
    __bot_tree: NameSpaceNode = NameSpaceNode(
        name=CMD.ROOT,
        children_node=[
            ExecutableNode(
                name=CMD.PLUGINS, source=make_installed_plugins_cmd(plugins_view=__bot.get_installed_plugins)
            ),
            ExecutableNode(name=CMD.HELP, source=make_help_cmd(client=__bot.root)),
            ExecutableNode(name=CMD.VERSION, source=lambda: DefaultConfig.VERSION.value),
        ],
        help_message="BotInfo provided",
    )
    __bot.root.add_node(__bot_tree)

    @classmethod
    def init(cls):
        cls.__bot.init_utils()

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

    bot.init()
    bot.run()
