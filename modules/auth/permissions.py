from abc import ABCMeta
from typing import TypeVar, Set, final


class PermissionBase(metaclass=ABCMeta):
    _id: int

    __permission_labels: Set[str] = set()

    def __init__(self, permission_name: str, permission_label: str):
        if permission_label in self.__permission_labels:
            raise ValueError(f"Permission label {permission_label} is already defined")
        self.__permission_labels.add(permission_label)
        self._permission_label = permission_label

        self._name = permission_name

    @final
    @property
    def id(self) -> int:
        """
        Returns the ID of the object.

        Returns:
            An integer representing the ID of the object.

        Raises:
            AttributeError: If the object does not have an attribute names '_id'.
        """
        if not hasattr(self, "_id"):
            raise AttributeError(f"{self.__class__.__name__} has no attribute '_id', you must define it.")
        return self._id

    @final
    @property
    def name(self) -> str:
        """
        Returns the name of the object.

        Returns:
            A string representing the name of the object.

        Raises:
            AttributeError: If the object does not have an attribute names '_name'.
        """
        if not hasattr(self, "_name"):
            raise AttributeError(f"{self.__class__.__name__} has no attribute '_name', you must define it.")
        return self._name

    @final
    def __eq__(self, other: "PermissionBase") -> bool:
        return self._id == other._id and self._permission_label == other._permission_label


Permission = TypeVar("Permission", bound=PermissionBase)


class ReadPermission(PermissionBase):
    _id = 1


class ModifyPermission(PermissionBase):
    _id = 2


class DeletePermission(PermissionBase):
    _id = 4


class ExecutePermission(PermissionBase):
    _id = 8
