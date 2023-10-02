import copy
from typing import Any, FrozenSet, Iterable, NamedTuple, Set, Callable

from modules.auth.permissions import Permission, ReadPermission, ModifyPermission, DeletePermission, ExecutePermission


class RequiredPermissions(NamedTuple):
    read_permissions: FrozenSet[Permission] = frozenset([ReadPermission])
    modify_permissions: FrozenSet[Permission] = frozenset([ModifyPermission])
    execute_permissions: FrozenSet[Permission] = frozenset([ExecutePermission])
    delete_permissions: FrozenSet[Permission] = frozenset([DeletePermission])


class ResourceInfo(NamedTuple):
    name: str
    id: int
    label: str


class Resource(object):
    __resource_labels: Set[str] = set()

    def __init__(
        self,
        source: Any,
        resource_info: ResourceInfo,
        required_permissions: RequiredPermissions = RequiredPermissions(),
    ):
        if resource_info.label in self.__resource_labels:
            raise ValueError(f"Resource label {resource_info.label} is already defined")
        self.__resource_labels.add(resource_info.label)
        self._source: Any = copy.copy(source)
        self._resource_name: str = resource_info.name
        self._resource_id: int = resource_info.id
        self._resource_label: str = resource_info.label

        self._required_permissions: RequiredPermissions = required_permissions
        self._full_permissions: FrozenSet[Permission] = frozenset(set().union(*required_permissions))

    @property
    def name(self) -> str:
        return self._resource_name

    @property
    def id(self) -> int:
        return self._resource_id

    def get_source(self, permissions: Iterable[Permission]) -> Any | None:
        """
        Return the source of the object if the permissions passed as argument
        are a superset of the object's full permissions.

        Parameters:
            permissions (Iterable[Permission]): The permissions to check against.

        Returns:
            Any | None: The source of the object if permissions are valid, otherwise None.
        """
        if self._full_permissions.issubset(permissions):
            return self._source

    def get_read_access(self, permissions: Iterable[Permission]) -> Any | None:
        """
        Check if the given permissions allow read access and return a deepcopy of the source if they do.

        Parameters:
            permissions (Iterable[Permission]): The permissions to check against.

        Returns:
            Any | None: A deepcopy of the source if the permissions allow read access, None otherwise.
        """
        if self._required_permissions.read_permissions.issubset(permissions):
            return copy.deepcopy(self._source)

    def get_modify_access(self, permissions: Iterable[Permission], operation: Callable[[Any], Any]) -> Any | None:
        """
        Check if the given permissions allow modification and apply the specified operation on the source.

        Parameters:
            permissions (Iterable[Permission]): The permissions to check against.
            operation (Callable[[Any], Any]): The operation to apply on the source.

        Returns:
            Any | None: The result of the operation, or None if the permissions do not allow modification.

        Raises:
            RuntimeError: If the source address or type changes during the modification.
        """
        if not self._required_permissions.modify_permissions.issubset(permissions):
            return
        addr_before_modify = id(self._source)
        source_type_before_modify = type(self._source)
        operation_result = operation(self._source)
        addr_after_modify = id(self._source)
        source_type_after_modify = type(self._source)
        if addr_before_modify != addr_after_modify:
            raise RuntimeError(
                f"Source address changed during modification: {addr_before_modify} -> {addr_after_modify}"
            )
        elif source_type_before_modify != source_type_after_modify:
            raise RuntimeError(
                f"Source type changed during modification: {source_type_before_modify} -> {source_type_after_modify}"
            )
        else:
            return operation_result

    def get_excute_access(self, permissions: Iterable[Permission]) -> Any | None:
        """
        Checks if the user has execute access based on the given permissions.

        Args:
            permissions (Iterable[Permission]): The permissions to check against.

        Returns:
            Any | None: The result of executing the source function if the user has execute access,
            None otherwise.

        Raises:
            TypeError: If the source function is not callable.
        """
        if self._required_permissions.execute_permissions.issubset(permissions):
            if callable(self._source):
                return self._source()
            raise TypeError(f"{self._source} is not callable")

    def get_delete_access(self, permissions: Iterable[Permission]) -> None:
        """
        Determines if the user has delete access based on the given permissions.

        Args:
            permissions (Iterable[Permission]): The permissions to check against.

        Returns:
            None: If the user has delete access, the source is set to None.
        """
        if self._required_permissions.delete_permissions.issubset(permissions):
            self._source = None
