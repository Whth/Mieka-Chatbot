"""
plugin_base that is used in create a standard plugin
"""
from abc import ABC, abstractmethod
from graia.broadcast import Namespace, BaseDispatcher, Decorator, Dispatchable, Broadcast
from types import MappingProxyType
from typing import final, Callable, Type, List

from constant import CONFIG_FILE_NAME
from modules.auth.core import AuthorizationManager
from modules.cmd import NameSpaceNode
from modules.config_utils import ConfigRegistry


class AbstractPlugin(ABC):
    """
    Abstract plugin class
    """

    @final
    def __init__(
        self,
        plugins_viewer: MappingProxyType[str, "AbstractPlugin"],
        root_namespace_node: NameSpaceNode,
        broadcast: Broadcast,
        auth_manager: AuthorizationManager,
    ):
        self._auth_manager = auth_manager
        self._receiver = broadcast.receiver
        self._namespace: Namespace = broadcast.createNamespace(name=self.get_plugin_name())
        self._plugin_view: MappingProxyType[str, "AbstractPlugin"] = plugins_viewer
        self._config_registry: ConfigRegistry = ConfigRegistry(f"{self._get_config_parent_dir()}/{CONFIG_FILE_NAME}")
        self._root_namespace_node: NameSpaceNode = root_namespace_node

    @final
    def receiver(
        self,
        event: str | Type[Dispatchable],
        priority: int = 16,
        dispatchers: List[Type[BaseDispatcher] | BaseDispatcher] | None = None,
        decorators: list[Decorator] | None = None,
    ) -> Callable:
        """
        This function is a decorator used to register event listeners.
        It takes in the following parameters:

        - `event`: A string or a subclass of `Dispatchable`.
        This parameter represents the event that the decorated function wants to listen to.
        - `priority`: An integer representing the priority of the event listener.
            The higher the priority, the earlier listener be executed.
        - `dispatchers`: An optional list of dispatchers to be used for inline event dispatching.
        - `namespace`: An optional namespace to be used for the event listener.
        - `decorators`: An optional list of decorators to be applied to the decorated function.

        The function returns a wrapper function that registers the decorated function as an event listener.
        If the event listener already exists, an exception is raised.

        Example usage:

        ```
        @receiver("event_name", priority=10)
        def event_handler(event):
            # handle the event
        ```

        """
        return self._receiver(
            event=event, priority=priority, dispatchers=dispatchers, decorators=decorators, namespace=self._namespace
        )

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


PluginsView: Type = MappingProxyType[str, AbstractPlugin]
