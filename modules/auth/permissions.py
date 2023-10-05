from enum import Enum
from pydantic import root_validator
from typing import Dict, Any, Type, Iterable, FrozenSet

from .utils import AuthBaseModel, manager_factory, ManagerBase


class PermissionCode(Enum):
    Read: int = 1
    Execute: int = 2
    Modify: int = 4
    Delete: int = 8
    Special: int = 16
    Super: int = 32


class Permission(AuthBaseModel):
    __permission_categories__: Dict[int, str] = {
        PermissionCode.Read.value: "ReadPermission",
        PermissionCode.Execute.value: "ExecutePermission",
        PermissionCode.Modify.value: "ModifyPermission",
        PermissionCode.Delete.value: "DeletePermission",
        PermissionCode.Special.value: "SpecialPermission",
        PermissionCode.Super.value: "SuperPermission",
    }

    __cache__: Dict[FrozenSet, "Permission"] = {}

    def __new__(cls, **kwargs) -> "Permission":
        key = frozenset(kwargs.values())
        if key not in cls.__cache__:
            cls.__cache__[key] = super().__new__(cls)
        return cls.__cache__[key]

    @root_validator()
    def validate_all(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates all the parameters of the given dictionary and returns the validated dictionary.

        Parameters:
        - params (Dict[str, Any]): A dictionary containing the parameters to be validated.

        Returns:
        - Dict[str, Any]: A dictionary with the validated parameters.

        Raises:
        - KeyError: If the 'id' parameter is not a valid permission category.
        - ValueError: If the 'name' parameter is already in use.
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
