from typing import Optional, Dict, Type

from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import WebsocketClientConfig
from graia.ariadne.entry import config

from modules.plugin_base import AbstractPlugin


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
