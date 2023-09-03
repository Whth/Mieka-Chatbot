"""
plugin_base that is used in create a standard plugin
"""
from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import final

from graia.ariadne import Ariadne

from constant import CONFIG_FILE_NAME
from modules.config_utils import ConfigRegistry


class AbstractPlugin(ABC):
    """
    Abstract plugin class
    """

    @final
    def __init__(
        self,
        ariadne_app: Ariadne,
        plugins_viewer: MappingProxyType[str, "AbstractPlugin"],
    ):
        self._ariadne_app: Ariadne = ariadne_app
        self._plugin_view: MappingProxyType[str, "AbstractPlugin"] = plugins_viewer
        self._config_registry: ConfigRegistry = ConfigRegistry(f"{self._get_config_parent_dir()}/{CONFIG_FILE_NAME}")

    @abstractmethod
    def _get_config_parent_dir(self) -> str:
        """
        Get the config parent dir, absolute path
        :return:
        :rtype:
        """
        pass

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


PluginsView = MappingProxyType[str, AbstractPlugin]
