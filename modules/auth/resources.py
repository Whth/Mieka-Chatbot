import copy
from pydantic import Field, PrivateAttr
from typing import Any, List, Callable, Unpack, Iterable

from .permissions import Permission, auth_check
from .utils import AuthBaseModel


class RequiredPermission(AuthBaseModel):
    read: List[Permission] = Field(default_factory=list, unique_items=True)
    modify: List[Permission] = Field(default_factory=list, unique_items=True)
    execute: List[Permission] = Field(default_factory=list, unique_items=True)
    delete: List[Permission] = Field(default_factory=list, unique_items=True)


class Resource(AuthBaseModel):
    """
    Resource object.
    seal some kind of source, add permissions check when try to access it
    if **ANY** of the required permissions are present, return the access, raise a PermissionError otherwise
    """

    source: Any | None = Field(allow_mutation=True, exclude=True)
    required_permissions: RequiredPermission
    _source: Any = PrivateAttr(default=None)

    class Config:
        allow_mutation = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._source = self.source
        delattr(self, "source")

    def get_read(self, permissions: Iterable[Permission]) -> Any:
        """
        Returns a copy of the source if any of the read permissions are present in the provided permissions.
        Otherwise, raises a PermissionError.

        Args:
            permissions (Iterable[Permission]): An iterable of Permission objects.

        Returns:
            Any: A copy of the source if read permissions are present.

        Raises:
            PermissionError: If no read permissions are present.
        """
        if not self.required_permissions.read or any(
            read_perm in permissions for read_perm in self.required_permissions.read
        ):
            return copy.deepcopy(self._source)
        raise PermissionError("Illegal Read operation")

    def get_modify(self, permissions: Iterable[Permission], operation: Callable) -> Any:
        """
        Returns the result of performing a modify operation on the source object, if the user has the required permissions.

        Parameters:
            permissions (Iterable[Permission]): The permissions available to the user.
            operation (Callable): The modify operation to be performed on the source object.

        Returns:
            Any: The result of the modify operation on the source object.

        Raises:
            PermissionError: If the user does not have the required permissions for the modify operation.
        """
        if auth_check(self.required_permissions.modify, permissions):
            source_bak = copy.deepcopy(self._source)
            id_before_op = id(source_bak)
            type_before_op = type(source_bak)
            operation(source_bak)
            if id(source_bak) == id_before_op and type(source_bak) == type_before_op:
                return operation(self._source)
        raise PermissionError("Illegal Modify operation")

    def get_execute(self, permissions: Iterable[Permission], **execute_params: Unpack) -> Any:
        """
        Executes the given function if it is callable and the user has the required permissions.

        Args:
            permissions (Iterable[Permission]): The permissions required to execute the function.
            **execute_params (Unpack): The parameters to be passed to the function.

        Returns:
            Any: The result of executing the function.

        Raises:
            PermissionError: If the user does not have the required permissions to execute the function.
        """
        if callable(self._source) and auth_check(self.required_permissions.execute, permissions):
            return self._source(**execute_params)
        raise PermissionError("Illegal Execute operation")

    def get_delete(self, permissions: Iterable[Permission]) -> Any:
        """
        Get the delete operation based on the given permissions.

        Parameters:
            permissions (Iterable[Permission]): The permissions to check.

        Returns:
            Any: The result of the delete operation.

        Raises:
            PermissionError: If the delete operation is not allowed.
        """
        if auth_check(self.required_permissions.delete, permissions):
            self._source = None
        raise PermissionError("Illegal Delete operation")

    def get_full_access(self, permissions: Iterable[Permission]) -> Any:
        """
        Check if the given permissions allow full access to the resource.

        Parameters:
            permissions (Iterable[Permission]): The permissions to be checked.

        Returns:
            Any: The resource if the permissions allow full access.

        Raises:
            PermissionError: If the permissions do not allow full access.
        """
        if all(
            [
                auth_check(self.required_permissions.read, permissions),
                auth_check(self.required_permissions.modify, permissions),
                auth_check(self.required_permissions.execute, permissions),
                auth_check(self.required_permissions.delete, permissions),
            ]
        ):
            return self._source
        raise PermissionError("Illegal Full Access operation")

    def update_source(self, permissions: Iterable[Permission], source: Any):
        """
        Updates the source of the object if the user has full access.

        Args:
            permissions (Iterable[Permission]): The permissions of the user.
            source (Any): The new source to update.

        Returns:
            None
        """
        if self.get_full_access(permissions):
            self._source = source
