import os
from importlib import import_module
from types import MappingProxyType
from typing import Optional, Dict, Type, Sequence, List

from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import WebsocketClientConfig
from graia.ariadne.entry import config

from constant import MAIN, EXTENSION_DIR
from modules.plugin_base import AbstractPlugin

PluginsView = MappingProxyType[str, AbstractPlugin]


def get_all_sub_dirs(directory: str) -> List[str]:
    """

    Args:
        directory (str):

    Returns:

    """
    subdirectories = [
        name
        for name in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, name))
    ]
    return subdirectories


class ChatBot(object):
    """
    ChatBot class
    """

    def __init__(
        self,
        account_id: Optional[int] = None,
        bot_name: Optional[str] = None,
        verify_key: Optional[str] = None,
        websocket_config: WebsocketClientConfig = WebsocketClientConfig(),
    ):
        self._ariadne_app: Ariadne = Ariadne(
            config(account=account_id, verify_key=verify_key, *websocket_config)
        )

        self._bot_name: str = bot_name

        # init plugin installation registry dict and proxy
        self._installed_plugins: Dict[str, AbstractPlugin] = {}
        self._installed_plugins_proxy: PluginsView = MappingProxyType(
            self._installed_plugins
        )

    @property
    def get_installed_plugins(self) -> PluginsView:
        """
        Installed plugins
        Returns:

        """
        return self._installed_plugins_proxy

    def _install_all_extensions(self):
        """
        Install all extensions
        Returns:

        """
        detected_plugins = self._detect_plugins(EXTENSION_DIR)
        for plugin in detected_plugins:
            self._install_plugin(plugin)

    @staticmethod
    def _detect_plugins(extensions_path: str):
        """
        Detect plugins in the extension path
        :param extensions_path:
        :type extensions_path:
        :return:
        :rtype:
        """
        sub_dirs: List[str] = get_all_sub_dirs(extensions_path)
        detected_plugins: List[Type[AbstractPlugin]] = []
        for sub_dir in sub_dirs:
            extension_attr_chain: str = f"{extensions_path}.{sub_dir}"
            detected_plugins.extend(import_plugin(extension_attr_chain))
        return detected_plugins

    def _install_plugin(self, plugin: Type[AbstractPlugin]) -> None:
        """
        This code snippet defines a method called _install_plugin that takes a plugin parameter of type AbstractPlugin.
        It checks if the plugin is already registered and raises an error if it is.
        Then, it creates an instance of the plugin and calls its install method.
        Finally, it adds the plugin instance to a dictionary called _installed_plugins with the plugin name as the key.
        :param plugin:
        :type plugin:
        :return: None
        :rtype:
        """
        if plugin.get_plugin_name in self._installed_plugins:
            raise ValueError("Plugin already registered")
        plugin_instance = plugin(self._ariadne_app, self.get_installed_plugins)
        plugin_instance.install()
        self._installed_plugins[plugin.get_plugin_name()] = plugin_instance

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


def import_plugin(extension_attr_chain: str) -> Sequence[Type[AbstractPlugin]]:
    """
    load the extension and return the plugins in it
    :param extension_attr_chain:
    :type extension_attr_chain:
    :return:
    :rtype:

    notes:
        one extension is allowed to contain multiple extensions
    """

    module = import_module(MAIN, extension_attr_chain)  # load extension
    plugins: List[Type[AbstractPlugin]] = []  # init yield list

    for plugin_name in module.__all__:
        # load plugins
        plugin_name: str
        if not hasattr(module, plugin_name):
            # attr check
            raise ImportError(
                f"Plugin {plugin_name} not found in {extension_attr_chain}"
            )
        plugin: Type = getattr(module, plugin_name)
        if issubclass(plugin, AbstractPlugin):
            # check if plugin is subclass of AbstractPlugin
            plugins.append(plugin)

    return plugins
