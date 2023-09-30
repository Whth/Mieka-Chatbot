"""
plugin_base that is used in create a standard plugin
"""
from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import final, Callable, Type, List

from graia.ariadne import Ariadne
from graia.broadcast import Namespace, Broadcast, BaseDispatcher, Decorator, Dispatchable

from constant import CONFIG_FILE_NAME
from modules.config_utils import ConfigRegistry, CmdClient


class AbstractPlugin(ABC):
    """
    Abstract plugin class
    """

    @final
    def __init__(
        self,
        ariadne_app: Ariadne,
        plugins_viewer: MappingProxyType[str, "AbstractPlugin"],
        cmd_client: CmdClient,
        priority: int = 8,
    ):
        self._ariadne_app: Ariadne = ariadne_app
        self._broadcast: Broadcast = self._ariadne_app.broadcast
        self._namespace: Namespace = self._broadcast.createNamespace(name=self.get_plugin_name(), priority=priority)

        self._plugin_view: MappingProxyType[str, "AbstractPlugin"] = plugins_viewer
        self._config_registry: ConfigRegistry = ConfigRegistry(f"{self._get_config_parent_dir()}/{CONFIG_FILE_NAME}")
        self._cmd_client: CmdClient = cmd_client

    @final
    def receiver(
        self,
        func: Callable,
        event: str | Type[Dispatchable],
        priority: int = 16,
        dispatchers: List[Type[BaseDispatcher] | BaseDispatcher] | None = None,
        decorators: list[Decorator] | None = None,
    ) -> None:
        """
        Registers a function as a receiver for a specific event.

        Args:
            func (Callable): The function to be registered as a receiver.
            event (str | Type[Dispatchable]): The event that the function will listen to.
            priority (int, optional): The priority of the receiver. Defaults to 16.
            dispatchers (List[Type[BaseDispatcher] | BaseDispatcher] | None, optional):
                The dispatchers that the receiver will be associated with. Defaults to None.
            decorators (list[Decorator] | None, optional):
                The decorators to be applied to the receiver function. Defaults to None.

        Returns:
            None: This function does not return anything.
        """
        self._broadcast.receiver(
            event=event, priority=priority, dispatchers=dispatchers, decorators=decorators, namespace=self._namespace
        )(func)

    @final
    @property
    def namespace(self) -> Namespace:
        """

        Returns: the namespace of the object.

        """
        return self._namespace

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

    @final
    def uninstall(self):
        """
        Uninstall the plugin
        """
        self._namespace.disabled = True
        self._broadcast.removeNamespace(self._namespace.name)


PluginsView: Type = MappingProxyType[str, AbstractPlugin]
