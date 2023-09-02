import os
from importlib import import_module
from typing import Optional, Dict, Type, Sequence, List

from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import WebsocketClientConfig
from graia.ariadne.entry import config

from constant import MAIN
from modules.plugin_base import AbstractPlugin


def list_directories(directory):
    abs_directory = os.path.abspath(directory)
    directories = [os.path.join(abs_directory, name) for name in os.listdir(abs_directory) if os.path.isdir(os.path.join(abs_directory, name))]
    return directories

class ChatBot(object):
    """
    ChatBot class
    """

    def __init__(self,
                 account_id: Optional[int] = None,
                 bot_name: Optional[str] = None,
                 verify_key: Optional[str] = None,
                 websocket_config: WebsocketClientConfig = WebsocketClientConfig()):
        self._ariadne_app: Ariadne = Ariadne(config(
            account=account_id,
            verify_key=verify_key,
            *websocket_config
        ))

        self._bot_name: str = bot_name

        self._plugins: Dict[str, AbstractPlugin] = {}

    def _detect_plugins(self,extension_path:str):
        """
        Detect plugins in the extension path
        :param extension_path:
        :type extension_path:
        :return:
        :rtype:
        """
        for file in os.listdir(extension_path):


    def add_plugin(self, plugin: Type[AbstractPlugin]) -> None:
        """

        :param plugin:
        :type plugin:
        :return: None
        :rtype:
        """
        if plugin.get_plugin_name in self._plugins:
            raise ValueError("Plugin already registered")
        plugin_instance = plugin(self._ariadne_app)
        plugin_instance.install()
        self._plugins[plugin.get_plugin_name()] = plugin_instance

    def run(self) -> None:
        """
        Run the bot
        """
        self._ariadne_app.launch_blocking()

    def stop(self) -> None:
        """
        Stop the bot
        """
        self._ariadne_app.stop()





def import_plugin(extension_dir_path: str) -> Sequence[Type[AbstractPlugin]]:
    """
    load the extension and return the plugins in it
    :param extension_dir_path:
    :type extension_dir_path:
    :return:
    :rtype:

    notes:
        one extension is allowed to contain multiple extensions
    """

    module = import_module(MAIN, extension_dir_path)  # load extension
    plugins: List[Type[AbstractPlugin]] = []  # init yield list

    for plugin_name in module.__all__:
        # load plugins
        plugin_name: str
        if not hasattr(module, plugin_name):
            # attr check
            raise ImportError(f'Plugin {plugin_name} not found in {extension_dir_path}')
        plugin: Type = getattr(module, plugin_name)
        if issubclass(plugin, AbstractPlugin):
            # check if plugin is subclass of AbstractPlugin
            plugins.append(plugin)

    return plugins
