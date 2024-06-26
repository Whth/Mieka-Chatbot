import pathlib
from enum import Enum
from typing import List

from graia.ariadne.connection.config import WebsocketClientConfig

from constant import CONFIG_FILE_NAME, CONFIG_DIR, EXTENSION_DIR
from modules.auth.resources import RequiredPermission
from modules.chat_bot import ChatBot, BotInfo, BotConfig, BotConnectionConfig
from modules.cmd import ExecutableNode, NameSpaceNode
from modules.config_utils import ConfigRegistry
from modules.shared import EnumCMD


class DefaultConfig(Enum):
    WEBSOCKET_HOST = "http://127.0.0.1:8080"
    AUTH_CONFIG_FILE_NAME: str = f"{CONFIG_DIR}/auth_manager.json"
    VERIFY_KEY = "INITKEYXBVCdNG0"
    ACCOUNT_ID = 1234567890
    ACCEPTED_MESSAGE_TYPES = ["GroupMessage"]
    VERSION = "v0.5.1"


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


class CMD(EnumCMD):
    bot = ["b", "bt"]
    version = ["v", "V", "ver"]
    plugins = ["pl", "plg", "plug"]
    cmds = ["c", "cds"]
    disable = ["di", "dis"]
    enable = ["en", "ena"]
    reboot = ["r", "rbt"]
    superuser = ["su"]


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

    def __init__(self):
        bot_tree: NameSpaceNode = NameSpaceNode(
            **CMD.bot.export(),
            children_node=[
                ExecutableNode(
                    **CMD.plugins.export(),
                    source=make_installed_plugins_cmd(plugins_view=self.__bot.get_installed_plugins),
                ),
                ExecutableNode(
                    **CMD.cmds.export(),
                    source=make_help_cmd(client=self.__bot.root),
                    help_message="These cmds are both built-in and extensions",
                ),
                ExecutableNode(
                    **CMD.version.export(),
                    source=lambda: DefaultConfig.VERSION.value,
                    help_message="The core version of the bot",
                ),
                ExecutableNode(
                    **CMD.disable.export(),
                    help_message="Disable the target plugin",
                    source=lambda x: f'Disable the "{x}" plugin\nSuccess={self.__bot.extensions.disable_plugin(x)}',
                ),
                ExecutableNode(
                    **CMD.enable.export(),
                    help_message="Enable the target plugin",
                    source=lambda x: f'Enable the "{x}" plugin\nSuccess={self.__bot.extensions.enable_plugin(x)}',
                ),
                ExecutableNode(
                    **CMD.reboot.export(),
                    required_permissions=RequiredPermission(execute=[self.__bot.auth_manager.__su_permission__]),
                    help_message="Reboot the bot",
                    source=lambda: f"Reboot the bot\nSuccess={self.__bot.reboot()}",
                ),
            ],
            help_message="ChatBot coral management tool",
        )
        self.__bot.root.add_node(bot_tree)

    @classmethod
    def run(cls):
        """
        run the bot, save config_registry on exit
        Returns:

        """

        cls.__bot.run(init_utils=True)

    @classmethod
    def init_utils(cls):
        cls.__bot.init_utils()


import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--test", action="store_true", help="test mode", default=False)

if __name__ == "__main__":
    args = parser.parse_args()
    print(args)
    bot = Mieka()
    if args.test:
        print("test mode")
        try:
            bot.init_utils()
        except Exception as e:
            print(e)
            exit(1)
        print("test mode done")
        exit(0)

    bot.run()
