import pathlib
from importlib import import_module
from types import MappingProxyType
from typing import List, Dict, Type, Sequence

from colorama import Fore, Back, Style
from graia.broadcast import Broadcast

from constant import REQUIREMENTS_FILE_NAME, MAIN
from modules.config_utils import CmdClient
from modules.file_manager import get_all_sub_dirs
from modules.launch_utils import install_requirements
from modules.plugin_base import AbstractPlugin, PluginsView


class ExtensionManager:
    def __init__(self, extension_dir: str, black_list: List[str]):
        self._plugins: Dict[str, AbstractPlugin] = {}
        self._black_list: List[str] = black_list
        pathlib.Path(extension_dir).mkdir(parents=True, exist_ok=True)
        self._extension_dir: str = extension_dir

    @property
    def plugins(self) -> Dict[str, AbstractPlugin]:
        """
        Returns the dictionary of plugins registered with this object.

        :return: A dictionary mapping plugin names to plugin instances.
        :rtype: Dict[str, AbstractPlugin]
        """
        return self._plugins

    @property
    def plugins_view(self) -> PluginsView:
        """
        Returns a read-only view of the plugin dictionary.

        :return: A read-only view of the plugin dictionary.
        :rtype: MappingProxyType[str, AbstractPlugin]
        """
        return MappingProxyType(self._plugins)

    def install_all_extensions(self, broadcast: Broadcast, bot_client: CmdClient, proxy: PluginsView) -> None:
        """
        Installs all extensions for the given app and bot client.

        Args:

            broadcast ():
            bot_client (CmdClient): The bot client instance.
            proxy (MappingProxyType[str, AbstractPlugin]): The proxy mapping of plugin names to plugin instances.

        Returns:
            None: This function does not return anything.

        Raises:
            None: This function does not raise any exceptions.
        """
        detected_plugins = self._detect_plugins()
        string_buffer = "\n".join(
            [
                f"{Fore.YELLOW}{Back.BLACK}|{plugin.get_plugin_name():<16}|"
                f"{plugin.get_plugin_version():<8}|"
                f"{plugin.get_plugin_author():<10}|"
                f"{plugin.get_plugin_description():<80}|{Style.RESET_ALL}"
                for plugin in detected_plugins
            ]
        )
        print(Fore.GREEN + Back.RED + f"Detected {len(detected_plugins)} plugins: " + Style.RESET_ALL)
        labels = ["Extension", "Version", "Author", "Description"]
        print(
            Fore.CYAN
            + Back.BLACK
            + f"|{labels[0]:^16}|{labels[1]:^8}|{labels[2]:^10}|{labels[3]:^80}|"
            + Style.RESET_ALL
        )
        print(string_buffer)
        for plugin in detected_plugins:
            if plugin.get_plugin_name() in self._black_list:
                continue
            print(Fore.LIGHTRED_EX)
            self.install_plugin(plugin, broadcast, bot_client, proxy)
            print(Fore.RESET)

    def install_plugin(
        self,
        plugin: Type[AbstractPlugin],
        broadcast: Broadcast,
        bot_client: CmdClient,
        proxy: PluginsView,
    ) -> None:
        """
        Installs a plugin into the system.

        Args:
            plugin (Type[AbstractPlugin]): The plugin class to be installed.

            bot_client (CmdClient): The bot client instance.
            proxy (MappingProxyType[str, AbstractPlugin]): The proxy object for accessing other plugins.

        Returns:
            None

        Raises:
            ValueError: If the plugin is already registered.
        """
        if plugin.get_plugin_name in self._plugins:
            raise ValueError("Plugin already registered")
        plugin_instance = plugin(proxy, bot_client, broadcast)

        plugin_instance.install()
        self._plugins[plugin.get_plugin_name()] = plugin_instance
        print(
            f"{Fore.GREEN}Installed {plugin.get_plugin_name()}\n"
            f"{Fore.MAGENTA}----------------------------------------------\n"
        )

    def uninstall_plugin(self, plugin_name: str) -> None:
        if plugin_name in self._plugins:
            self._plugins.get(plugin_name).uninstall()

    def install_all_requirements(self):
        detected_requirements = self._detect_requirements()
        for requirement_file in detected_requirements:
            install_requirements(requirement_file)

    def _detect_plugins(self) -> List[Type[AbstractPlugin]]:
        sub_dirs: List[str] = get_all_sub_dirs(self._extension_dir)
        detected_plugins: List[Type[AbstractPlugin]] = []
        for sub_dir in sub_dirs:
            extension_attr_chain: str = f"{self._extension_dir}.{sub_dir}"
            detected_plugins.extend(self._import_plugin(extension_attr_chain))
        return detected_plugins

    def _detect_requirements(self) -> List[str]:
        sub_dirs: List[str] = get_all_sub_dirs(self._extension_dir)
        detected_requirements: List[str] = []
        for sub_dir in sub_dirs:
            requirement_file_path = f"{self._extension_dir}/{sub_dir}/{REQUIREMENTS_FILE_NAME}"
            if pathlib.Path(requirement_file_path).exists():
                detected_requirements.append(requirement_file_path)
        return detected_requirements

    @staticmethod
    def _import_plugin(extension_attr_chain: str) -> Sequence[Type[AbstractPlugin]]:
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
