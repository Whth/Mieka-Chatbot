import copy
import random
from pydantic import Field, PrivateAttr, BaseModel
from typing import Any, List, Callable, Unpack, Iterable, Optional, Type, Dict

from .permissions import Permission, auth_check, PermissionCode
from .utils import AuthBaseModel, ManagerBase


class RequiredPermission(BaseModel):
    class Config:
        allow_mutation = False
        validate_assignment = True

    read: List[Permission] = Field(default_factory=list, unique_items=True)
    modify: List[Permission] = Field(default_factory=list, unique_items=True)
    execute: List[Permission] = Field(default_factory=list, unique_items=True)
    delete: List[Permission] = Field(default_factory=list, unique_items=True)
    super: List[Permission] = Field(default_factory=list, unique_items=True)

    def add_permission(self, permission: Permission, category_name: str) -> None:
        perm_list: List[Permission] = getattr(self, category_name)
        perm_list.append(permission)


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
    super_permissions: Optional[List[Permission]] = None,
) -> RequiredPermission:
    """
    Generate a RequiredPermission object based on the given parameters.

    This function takes in the following parameters:
    - target_resource_name: A string representing the name of the target resource.
    - extra_permissions(optional): A list of Permission objects representing any additional permissions.
    - required_perm_name (optional): A string representing the name of the required permission.
        If not provided, it will be generated based on the target_resource_name.
    - required_perm_id (optional): An integer representing the ID of the required permission.
        If not provided, it will be randomly generated using the random_digits function.


    The function returns a RequiredPermission object that contains the following attributes:
    - id: An integer representing the ID of the required permission.
    - name: A string representing the name of the required permission.
    - read: A list of Permission objects representing the read permissions.
    - modify: A list of Permission objects representing the modify permissions.
    - execute: A list of Permission objects representing the execute permissions.
    - delete: A list of Permission objects representing the delete permissions.
    """
    super_permissions = super_permissions or []
    return RequiredPermission(
        read=[Permission(id=PermissionCode.ReadPermission.value, name=target_resource_name)],
        modify=[Permission(id=PermissionCode.ModifyPermission.value, name=target_resource_name)],
        execute=[Permission(id=PermissionCode.ExecutePermission.value, name=target_resource_name)],
        delete=[Permission(id=PermissionCode.DeletePermission.value, name=target_resource_name)],
        super=super_permissions,
    )


class Resource(AuthBaseModel):
    """
    Resource object.
    seal some kind of source, add permissions check when try to access it
    if **ANY** of the required permissions are present, return the access, raise a PermissionError otherwise
    """

    source: Any | None = Field(default=None, allow_mutation=True, exclude=True)
    required_permissions: RequiredPermission
    _source: Any = PrivateAttr(default=None)
    _is_deleted: bool = PrivateAttr(default=True)

    class Config:
        allow_mutation = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.source:
            self._is_deleted = False
            self._source = self.source
        delattr(self, "source")

    def get_read(self, permissions: Iterable[Permission]) -> Any:
        """
        Get the read permission for the object.

        Parameters:
            permissions (Iterable[Permission]): The permissions to check.

        Returns:
            Any: The read permission if it is allowed.

        Raises:
            PermissionError: If the read operation is not allowed.
        Note:
            if the source is callable, it will never be returned
        """
        if callable(self._source):
            raise PermissionError("Illegal Read operation, executable resource cannot be accessed in read")

        if auth_check(self.required_permissions.read, permissions, optional_super=self.required_permissions.super):
            return copy.deepcopy(self._source)
        raise PermissionError("Illegal Read operation, insufficient permissions")

    def get_modify(self, permissions: Iterable[Permission], operation: Callable, **modify_params: Unpack) -> None:
        """
        Get and modify the source object using the given operation and modify parameters.

        Parameters:
            permissions (Iterable[Permission]): The permissions required to perform the modify operation.
            operation (Callable): The operation to be performed on the source object.
            **modify_params (Unpack): Additional parameters for the modify operation.

        Returns:


        Raises:
            PermissionError: If the required permissions are not satisfied.
        """

        if auth_check(self.required_permissions.modify, permissions, optional_super=self.required_permissions.super):
            operation(self._source, **modify_params)
            return
        raise PermissionError("Illegal Modify operation, insufficient permissions")

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

        if auth_check(self.required_permissions.execute, permissions, optional_super=self.required_permissions.super):
            return self._source(**execute_params)
        raise PermissionError("Illegal Execute operation, insufficient permissions")

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
        if self._is_deleted:
            raise PermissionError("Illegal Delete operation, resource already deleted")
        if auth_check(self.required_permissions.delete, permissions, optional_super=self.required_permissions.super):
            del self._source
            self._source = None
            self._is_deleted = True
            return
        raise PermissionError("Illegal Delete operation, insufficient permissions")

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
        if auth_check(self.required_permissions.super, permissions) or all(
            [
                auth_check(self.required_permissions.read, permissions),
                auth_check(self.required_permissions.modify, permissions),
                auth_check(self.required_permissions.execute, permissions),
                auth_check(self.required_permissions.delete, permissions),
            ]
        ):
            return self._source
        raise PermissionError("Illegal Full Access operation, insufficient permissions")

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


class ResourceManager(ManagerBase):
    ele_type: Type[Resource] = Field(default=Resource, exclude=True, const=True)
    object_dict: Dict[str, Resource] = Field(default_factory=dict, const=True)

    def _make_object_instance(self, **kwargs) -> Resource:
        return self.ele_type(**kwargs)

    def _make_json_dict(self) -> Dict:
        return {self._root_key: [object_instance.dict() for object_instance in self.object_dict.values()]}

    def update_sources(self, su_permissions: Iterable[Permission], source_dict: Dict[str, Any]):
        """
        Update the sources in the object dictionary with the given permissions and source dictionary.

        Parameters:
            su_permissions (Iterable[Permission]): The permissions required to update the sources.
            source_dict (Dict[str, Any]): The dictionary containing the sources to be updated.

        Raises:
            KeyError: If any key in the source dictionary is not found in the object dictionary.

        Returns:
            None
        """
        if any(key not in self.object_dict for key in source_dict):
            raise KeyError("Invalid update, some Key(s) not found in object_dict")
        for key, value in source_dict.items():
            self.object_dict[key].update_source(su_permissions, value)
