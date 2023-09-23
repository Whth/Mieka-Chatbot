import os
from importlib import import_module
from types import MappingProxyType
from typing import Dict, Type, Sequence, List, NamedTuple, Any, Union

from colorama import Fore, Back, Style
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import WebsocketClientConfig
from graia.ariadne.entry import config
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Friend, Member, Stranger

from constant import MAIN, REQUIREMENTS_FILE_NAME
from modules.config_utils import CmdClient
from modules.file_manager import get_all_sub_dirs
from modules.launch_utils import run_pip_install, requirements_met
from modules.plugin_base import AbstractPlugin, PluginsView


class BotInfo(NamedTuple):
    """
    Represents information about a bot.

    Attributes:
        account_id (int): The ID of the bot's account.
        bot_name (str, optional): The name of the bot. Defaults to an empty string.
    """

    account_id: int
    bot_name: str = ""


class BotConnectionConfig(NamedTuple):
    """
    Represents the connection configuration for a bot.

    Attributes:
        verify_key (str): The verification key for the connection.
        websocket_config (WebsocketClientConfig, optional): The configuration for the WebSocket client.
        Default to WebsocketClientConfig().
    """

    verify_key: str
    websocket_config: WebsocketClientConfig = WebsocketClientConfig()


class BotConfig(NamedTuple):
    """
    Represents the configuration for a bot.

    Attributes:
        extension_dir (str): The directory where the bot's extensions are located.
        syntax_tree (Dict[str, Any]): The syntax tree used by the bot.
        accepted_message_types (List[str], optional): The types of messages accepted by the bot.
         Defaults to ["GroupMessage"].
    """

    extension_dir: str
    syntax_tree: Dict[str, Any]
    accepted_message_types: List[str] = ["GroupMessage"]


class ChatBot(object):
    """
    ChatBot class
    """

    @property
    def client(self) -> CmdClient:
        return self._bot_client

    def __init__(self, bot_info: BotInfo, bot_config: BotConfig, bot_connection_config: BotConnectionConfig):
        self._ariadne_app: Ariadne = Ariadne(
            config(bot_info.account_id, bot_connection_config.verify_key, bot_connection_config.websocket_config)
        )

        self._bot_name: str = bot_info.bot_name
        self._bot_client: CmdClient = CmdClient(
            bot_config.syntax_tree
        )  # TODO parse this instance to very plugin, to let them able to register cmd

        # init plugin installation registry dict and proxy
        self._installed_plugins: Dict[str, AbstractPlugin] = {}
        self._installed_plugins_proxy: PluginsView = MappingProxyType(self._installed_plugins)
        self._bot_config: BotConfig = bot_config

        async def _bot_client_call(target: Union[Group, Friend, Member, Stranger], message: MessageChain):
            """
            Asynchronously calls the bot client to send a message to the specified target.

            Args:
                target (Union[Group, Friend, Member, Stranger]): The target to send the message to.
                message (MessageChain): The message to send.

            Returns:
                None
            """
            try:
                stdout = self._bot_client.interpret(str(message))
            except KeyError:
                return
            (await self._ariadne_app.send_message(target, message=stdout)) if stdout else None

        for message_type in bot_config.accepted_message_types:
            self._ariadne_app.broadcast.receiver(message_type)(_bot_client_call)

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
            print(Fore.LIGHTRED_EX)
            self._install_plugin(plugin)
            print(Fore.RESET)

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
        plugin_instance = plugin(self._ariadne_app, self.get_installed_plugins, self._bot_client)

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
        Runs the function.

        This function is responsible for executing the main logic of the program.
        It performs the following steps:

        1. Install all the requirements by calling `_install_all_requirements()` with the `extension_dir` parameter.
        2. Install all the extensions by calling `_install_all_extensions()` with the `extension_dir` parameter.
        3. Retrieve the `Broadcast` object from the `_ariadne_app` attribute.
        4. Posts an `AllExtensionsInstalledEvent()` event to the broadcast.
        5. Launches the `_ariadne_app` in blocking mode.

        If a `KeyboardInterrupt` exception is raised during the execution, the function will call `stop()`
        to stop the program.

        Parameters:


        Returns:
            None
        """
        self._install_all_requirements(self._bot_config.extension_dir)
        self._install_all_extensions(self._bot_config.extension_dir)

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
