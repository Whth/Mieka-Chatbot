from abc import ABCMeta
from typing import TypeVar, Set, final


class PermissionBase(metaclass=ABCMeta):
    _id: int

    __permission_names: Set[str] = set()

    @final
    def __init__(self, target_name: str):
        self._name = f"{target_name}-{self.__class__.__name__}"
        if self._name in self.__permission_names:
            raise ValueError(f"Permission name {self._name} is already defined")
        self.__permission_names.add(self._name)

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
        return self._name

    @final
    def __eq__(self, other: "PermissionBase") -> bool:
        return self._id == other._id and self._name == other._name


Permission = TypeVar("Permission", bound=PermissionBase)


class ReadPermission(PermissionBase):
    _id = 1


class ModifyPermission(PermissionBase):
    _id = 2


class DeletePermission(PermissionBase):
    _id = 4


class ExecutePermission(PermissionBase):
    _id = 8
