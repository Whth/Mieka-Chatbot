"""
plugin_base that is used in create a standard plugin
"""
from abc import ABC, abstractmethod
from functools import partial
from types import MappingProxyType
from typing import final, Callable, Type, List, Dict, TypeAlias, TypeVar

from graia.broadcast import Namespace, BaseDispatcher, Decorator, Dispatchable, Broadcast

from constant import Value, EXTENSION_CONFIG_DIR
from modules.auth.core import AuthorizationManager
from modules.auth.permissions import Permission, PermissionCode
from modules.auth.resources import required_perm_generator, RequiredPermission
from modules.cmd import NameSpaceNode
from modules.config_utils import ConfigRegistry

Plugin: TypeAlias = TypeVar("Plugin", bound="AbstractPlugin")
PluginsView: TypeAlias = MappingProxyType[str, Plugin]


class AbstractPlugin(ABC):
    """
    Abstract plugin class
    """

    DefaultConfig: Dict[str, Value] = {}

    @final
    @property
    def config_registry(self) -> ConfigRegistry:
        return self._config_registry

    @final
    @property
    def namespace(self) -> Namespace:
        """
        Returns: the namespace of the object.
        """
        return self._namespace

    @final
    @property
    def auth_manager(self) -> AuthorizationManager:
        return self._auth_manager

    @final
    @property
    def plugin_view(self) -> PluginsView:
        return self._plugin_view

    @final
    @property
    def root_namespace_node(self) -> NameSpaceNode:
        return self._root_namespace_node

    @final
    @property
    def required_permission(self) -> RequiredPermission:
        return self._req_perm

    @final
    @property
    def su_permission(self) -> Permission:
        return self._su_perm

    @final
    def __register_default_config(self):
        """
        Registers the default configuration settings.
        Returns:
            None
        """
        if not isinstance(self.DefaultConfig, dict):
            raise ValueError("DefaultConfig must be a dictionary")
        for items in self.DefaultConfig.items():
            self.config_registry.register_config(*items)

    def __init__(
        self,
        plugins_viewer: PluginsView,
        root_namespace_node: NameSpaceNode,
        broadcast: Broadcast,
        auth_manager: AuthorizationManager,
    ):
        self._auth_manager = auth_manager
        self._receiver = broadcast.receiver
        self._namespace: Namespace = broadcast.createNamespace(name=self.get_plugin_name(), disabled=True)
        self._namespace_uninstaller = broadcast.removeNamespace

        self._plugin_view: PluginsView = plugins_viewer
        self._config_registry: ConfigRegistry = ConfigRegistry(f"{EXTENSION_CONFIG_DIR}/{self.get_plugin_name()}.json")
        self._root_namespace_node: NameSpaceNode = root_namespace_node
        self.__register_default_config()
        self._config_registry.load_config()
        self._su_perm = Permission(
            id=PermissionCode.SuperPermission.value,
            name=self.get_plugin_name(),
        )
        self._req_perm: RequiredPermission = required_perm_generator(
            target_resource_name=self.get_plugin_name(),
            super_permissions=[self._su_perm],
        )
        self._auth_manager.add_perm_from_req(self._req_perm)

    @final
    def receiver(
        self,
        event: str | Type[Dispatchable] | List[Type[Dispatchable]],
        priority: int = 16,
        dispatchers: List[Type[BaseDispatcher] | BaseDispatcher] | None = None,
        decorators: list[Decorator] | None = None,
    ) -> Callable:
        """
        Decorates a function to be a receiver of events.

        Args:
            event (str | Type[Dispatchable] | List[Type[Dispatchable]]): The event or events to listen for.
            priority (int, optional): The priority of the receiver.
                Defaults to 16.
            dispatchers (List[Type[BaseDispatcher] | BaseDispatcher] | None, optional):
                The dispatchers to use for the receiver. Defaults to None.
            decorators (list[Decorator] | None, optional): The decorators to apply to the receiver. Defaults to None.

        Returns:
            Callable: The decorated receiver function.

        Raises:
            TypeError: If the event parameter is not of the correct type.
        """
        if event and isinstance(event, list):
            partial_receiver = partial(
                self._receiver,
                priority=priority,
                dispatchers=dispatchers,
                decorators=decorators,
                namespace=self._namespace,
            )

            def merged_receiver(callable_target: Callable) -> Callable:
                for sub_event in event:
                    partial_receiver(sub_event)(callable_target)
                return callable_target

            return merged_receiver

        return self._receiver(
            event=event, priority=priority, dispatchers=dispatchers, decorators=decorators, namespace=self._namespace
        )

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
    def enable(self):
        """
        Enable the plugin
        """
        self._namespace.disabled = False

    @final
    def disable(self):
        """
        Disable the plugin
        """
        self._namespace.disabled = True

    @final
    def uninstall(self):
        self.disable()
        self._namespace_uninstaller(self._namespace.name)
        self.extra_uninstall()

    def extra_uninstall(self):
        """
        A description of the extra_uninstall function.
        """
        pass
