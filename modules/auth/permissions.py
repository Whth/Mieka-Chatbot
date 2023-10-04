from enum import Enum
from pydantic import validator, root_validator
from typing import Dict, Any, Set, Type, Iterable

from .utils import AuthBaseModel, manager_factory, ManagerBase


class PermissionCode(Enum):
    ReadPermission: int = 1
    ExecutePermission: int = 2
    ModifyPermission: int = 4
    DeletePermission: int = 8
    SpecialPermission: int = 16


class Permission(AuthBaseModel):
    __permission_categories__: Dict[int, str] = {
        PermissionCode.ReadPermission: "ReadPermission",
        PermissionCode.ExecutePermission: "ExecutePermission",
        PermissionCode.ModifyPermission: "ModifyPermission",
        PermissionCode.DeletePermission: "DeletePermission",
        PermissionCode.SpecialPermission: "SpecialPermission",
    }

    # TODO such unique validator is not good enough
    __permission_names__: Set[str] = set()

    @root_validator()
    def validate_all(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        A root validator function that validates all the parameters and returns a dictionary of validated parameters.

        Args:
            cls (Type): The class object.
            params (Dict[str, Any]): A dictionary of parameters to be validated.

        Returns:
            Dict[str, Any]: A dictionary of validated parameters.

        Raises:
            None
        """
        if params["id"] not in cls.__permission_categories__:
            raise KeyError(
                f"{params['id']} is not a valid permission category,"
                f" must be one of {list[cls.__permission_categories__.keys()]}"
            )
        suffix = f'{cls.__permission_categories__[params["id"]]}'
        true_name: str = f"{params['name']}{suffix}" if suffix not in params["name"] else params["name"]
        params["name"] = true_name
        return params

    @validator("name")
    def validate_name(cls, name: str) -> str:
        """
        Validates the given name.

        Args:
            cls (Type): The class that the method is defined on.
            name (str): The name to be validated.

        Returns:
            str: The validated name.
        """
        if name not in cls.__permission_names__:
            cls.__permission_names__.add(name)

        return name


PermissionManager: Type[ManagerBase] = manager_factory(Permission)


def auth_check(
    required_permissions: Iterable[Permission], query_permissions: Iterable[Permission], all_required: bool = False
) -> bool:
    """
    Check if the given query permissions match the required permissions.

    Args:
        required_permissions (Iterable[Permission]): The required permissions.
        query_permissions (Iterable[Permission]): The query permissions to check.
        all_required (bool, optional): Whether all the required permissions are needed. Defaults to False.

    Returns:
        bool: True if the query permissions match the required permissions, False otherwise.
    Notes:
        if the required permissions are empty, will immediately return True
    """

    operator = all if all_required else any
    return not required_permissions or operator(read_perm in query_permissions for read_perm in required_permissions)
