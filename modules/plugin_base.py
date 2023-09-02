from abc import ABC, abstractmethod
from typing import final

from graia.ariadne import Ariadne

from chat_bot import PluginsView


class AbstractPlugin(ABC):
    """
    Abstract plugin class
    """

    @final
    def __init__(self, ariadne_app: Ariadne, plugins_viewer: PluginsView):
        self._ariadne_app: Ariadne = ariadne_app
        self._plugin_view: PluginsView = plugins_viewer

    @classmethod
    @abstractmethod
    def get_plugin_name(cls) -> str:
        """
        Get the plugin name
        :return:
        :rtype:
        """
        pass

    @classmethod
    @abstractmethod
    def get_plugin_description(cls) -> str:
        """
        Get the plugin description
        :return:
        :rtype:
        """
        pass

    @classmethod
    @abstractmethod
    def get_plugin_version(cls) -> str:
        """
        Get the plugin version
        :return:
        :rtype:
        """
        pass

    @classmethod
    @abstractmethod
    def get_plugin_author(cls) -> str:
        """
        Get the plugin author
        :return:
        :rtype:
        """
        pass

    @abstractmethod
    def install(self):
        """
        Install the plugin
        """
        pass
