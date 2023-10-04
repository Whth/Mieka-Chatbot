import copy
import random
from pydantic import Field, PrivateAttr
from typing import Any, List, Callable, Unpack, Iterable, Optional

from .permissions import Permission, auth_check, PermissionCode
from .utils import AuthBaseModel


class RequiredPermission(AuthBaseModel):
    read: List[Permission] = Field(default_factory=list, unique_items=True)
    modify: List[Permission] = Field(default_factory=list, unique_items=True)
    execute: List[Permission] = Field(default_factory=list, unique_items=True)
    delete: List[Permission] = Field(default_factory=list, unique_items=True)


def random_digits(digits: int) -> int:
    """
    Generate a random integer with the specified number of digits.

    Parameters:
    - digits (int): The number of digits in the generated random integer.

    Returns:
    - int: The randomly generated integer.

    Example:
    - random_digits(3) returns 547
    """
    return int("".join([str(random.randint(0, 9)) for _ in range(digits)]))


def required_perm_generator(
    target_resource_name: str,
    extra_permissions: Optional[List[Permission]] = None,
    required_perm_name: Optional[str] = None,
    required_perm_id: Optional[int] = random_digits(5),
) -> RequiredPermission:
    """
    Generate a RequiredPermission object based on the given parameters.

    This function takes in the following parameters:
    - target_resource_name: A string representing the name of the target resource.
    - extra_permissions(optional): A list of Permission objects representing any additional permissions.
    - required_perm_name (optional): A string representing the name of the required permission. If not provided, it will be generated based on the target_resource_name.
    - required_perm_id (optional): An integer representing the ID of the required permission. If not provided, it will be randomly generated using the random_digits function.

    The function returns a RequiredPermission object that contains the following attributes:
    - id: An integer representing the ID of the required permission.
    - name: A string representing the name of the required permission.
    - read: A list of Permission objects representing the read permissions.
    - modify: A list of Permission objects representing the modify permissions.
    - execute: A list of Permission objects representing the execute permissions.
    - delete: A list of Permission objects representing the delete permissions.
    """
    extra_permissions = extra_permissions or []
    return RequiredPermission(
        id=required_perm_id,
        name=required_perm_name or f"{target_resource_name}RequiredPermission",
        read=[Permission(id=PermissionCode.Read.value, name=target_resource_name)] + extra_permissions,
        modify=[Permission(id=PermissionCode.Modify.value, name=target_resource_name)] + extra_permissions,
        execute=[Permission(id=PermissionCode.Execute.value, name=target_resource_name)] + extra_permissions,
        delete=[Permission(id=PermissionCode.Delete.value, name=target_resource_name)] + extra_permissions,
    )


class Resource(AuthBaseModel):
    """
    Resource object.
    seal some kind of source, add permissions check when try to access it
    if **ANY** of the required permissions are present, return the access, raise a PermissionError otherwise
    """

    source: Any | None = Field(allow_mutation=True, exclude=True)
    required_permissions: RequiredPermission
    _source: Any = PrivateAttr(default=None)
    _is_deleted: bool = PrivateAttr(default=False)

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
        if auth_check(self.required_permissions.read, permissions):
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
            if id(source_bak) != id_before_op or type(source_bak) != type_before_op:
                raise RuntimeError("Illegal Modify operation, you shouldn't change the type or the id of the source")
            else:
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

        if auth_check(self.required_permissions.execute, permissions):
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
        if not self._is_deleted and auth_check(self.required_permissions.delete, permissions):
            del self._source
            self._source = None
            self._is_deleted = True
            return
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
            self._is_deleted = False
