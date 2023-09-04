import os
from importlib import import_module
from types import MappingProxyType
from typing import Optional, Dict, Type, Sequence, List

from colorama import Fore, Back, Style
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import WebsocketClientConfig
from graia.ariadne.entry import config

from constant import MAIN, EXTENSION_DIR, REQUIREMENTS_FILE_NAME
from modules.file_manager import get_all_sub_dirs
from modules.launch_utils import run_pip_install, requirements_met
from modules.plugin_base import AbstractPlugin, PluginsView


class ChatBot(object):
    """
    ChatBot class
    """

    def __init__(
        self,
        account_id: int,
        verify_key: str,
        bot_name: Optional[str] = None,
        websocket_config: WebsocketClientConfig = WebsocketClientConfig(),
    ):
        self._ariadne_app: Ariadne = Ariadne(config(account_id, verify_key, websocket_config))

        self._bot_name: str = bot_name

        # init plugin installation registry dict and proxy
        self._installed_plugins: Dict[str, AbstractPlugin] = {}
        self._installed_plugins_proxy: PluginsView = MappingProxyType(self._installed_plugins)

        self._install_all_requirements(EXTENSION_DIR)
        self._install_all_extensions(EXTENSION_DIR)

    @property
    def get_installed_plugins(self) -> PluginsView:
        """
        Installed plugins
        Returns:

        """
        return self._installed_plugins_proxy

    def _install_all_extensions(self, extension_dir: str) -> None:
        """
        Install all extensions
        Returns:

        """
        if not os.path.exists(extension_dir):
            os.makedirs(extension_dir)

        detected_plugins = self._detect_plugins(extension_dir)
        string_buffer = "\n".join(
            [
                f"|{plugin.get_plugin_name():<16}|"
                f"{plugin.get_plugin_version():<8}|"
                f"{plugin.get_plugin_author():<10}|"
                for plugin in detected_plugins
            ]
        )
        print(Fore.GREEN + Back.RED + f"Detected {len(detected_plugins)} plugins: " + Style.RESET_ALL)
        labels = ["Extension", "Version", "Author"]
        print(Fore.CYAN + Back.BLACK + f"|{labels[0]:<16}|{labels[1]:<8}|{labels[2]:<10}|" + Style.RESET_ALL)
        print(Fore.YELLOW + Back.BLACK + string_buffer + Style.RESET_ALL)
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
        print(
            f"{Fore.GREEN}Installed {plugin.get_plugin_name()}\n"
            f"{Fore.MAGENTA}----------------------------------------------\n"
        )

    @staticmethod
    def _detect_requirements(extensions_path: str) -> List[str]:
        """
        Detect requirements of the extensions
        Args:
            extensions_path ():

        Returns:

        """
        sub_dirs: List[str] = get_all_sub_dirs(extensions_path)
        detected_requirements: List[str] = []
        for sub_dir in sub_dirs:
            requirement_file_path = f"{extensions_path}/{sub_dir}/{REQUIREMENTS_FILE_NAME}"
            if not os.path.exists(requirement_file_path):
                continue
            detected_requirements.append(requirement_file_path)
        return detected_requirements

    @staticmethod
    def _install_requirements(
        requirement_file_path: str,
    ):
        dirname = os.path.dirname(requirement_file_path)
        if requirements_met(requirement_file_path):
            print(f"requirements for {dirname} is already satisfied")
            return
        print(
            run_pip_install(
                command=f"install -r {requirement_file_path}",
                desc=f"requirements for {dirname}",
            )
        )

    def _install_all_requirements(self, extension_dir):
        detected_requirements = self._detect_requirements(extension_dir)
        for requirement_file in detected_requirements:
            self._install_requirements(requirement_file)

    def run(self) -> None:
        """
        Run the bot
        """
        try:
            self._ariadne_app.launch_blocking()

        except KeyboardInterrupt:
            self.stop()

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
    try:
        module = import_module(MAIN, extension_attr_chain)  # load extension
    except ModuleNotFoundError:
        return []
    plugins: List[Type[AbstractPlugin]] = []  # init yield list

    for plugin_name in module.__all__:
        # load plugins
        plugin_name: str
        if not hasattr(module, plugin_name):
            # attr check
            raise ImportError(f"Plugin {plugin_name} not found in {extension_attr_chain}")
        plugin: Type = getattr(module, plugin_name)
        if issubclass(plugin, AbstractPlugin):
            # check if plugin is subclass of AbstractPlugin
            plugins.append(plugin)

    return plugins
