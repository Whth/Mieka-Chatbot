from pydantic import Field, validator, PrivateAttr
from typing import Tuple, Type, List

from .permissions import Permission
from .utils import AuthBaseModel, manager_factory, ManagerBase


class Role(AuthBaseModel):
    permissions: List[Permission] = Field(default_factory=list, unique_items=True, allow_mutation=False)
    __role_activated__: bool = PrivateAttr(default=False)

    class Config:
        allow_mutation = True

    # TODO this role enter restrict strategy is not good enough, since only one user at a time can have a role
    @validator("permissions", each_item=True)
    def validate_permissions(cls, permission: Permission) -> Permission:
        """
        Validates the permissions.

        Args:
            cls (type): The class of the validator.
            permission (Permission): The permission to validate.

        Returns:
            Permission: The validated permission.

        Raises:
            ValueError: If the permission is not an instance of Permission.
        """
        if isinstance(permission, Permission):
            return permission
        raise ValueError(f"Permission {permission} is not an instance of Permission")

    def add_permission(self, permission: Permission):
        """
        Adds a permission to the role.

        Args:
            permission (Permission): The permission to be added.

        Raises:
            KeyError: If the permission is already present in the role.

        Returns:
            None
        """

        if permission in self.permissions:
            raise KeyError(f"Role {self.name} already has permission {permission}")
        self.permissions.append(permission)

    def remove_permission(self, permission: Permission):
        """
        Remove a permission from the role.

        Args:
            permission (Permission): The permission to remove from the role.

        Raises:
            KeyError: If the role does not have the specified permission.

        Returns:
            None
        """

        if permission not in self.permissions:
            raise KeyError(f"Role {self.name} does not have permission {permission}")
        self.permissions.remove(permission)

    def __enter__(self) -> Tuple[Permission]:
        if self.__role_activated__:
            raise ValueError(f"Role {self.name} is already activated")
        self.__role_activated__ = True
        return tuple(self.permissions)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__role_activated__ = False

    def __contains__(self, item: Permission) -> bool:
        return item in self.permissions


RoleManager: Type[ManagerBase] = manager_factory(Role)
