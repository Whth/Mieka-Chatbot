from typing import Set, FrozenSet, Optional

from .permissions import Permission


class Role(object):
    def __init__(self, role_id: int, role_name: str, permissions: Optional[Set[Permission]] = None):
        self._permissions: Set[Permission] = permissions if permissions else set()
        self._id: int = role_id
        self._name: str = role_name

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def add_permission(self, permission: Permission):
        self._permissions.add(permission)

    def remove_permission(self, permission: Permission):
        if permission not in self._permissions:
            raise KeyError(f"Role {self._name} does not have permission {permission}")
        self._permissions.remove(permission)

    def __enter__(self) -> FrozenSet[Permission]:
        return frozenset(self._permissions)

    # TODO try to write something to eliminate nested "with" statements, let only one role be entered
    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def __contains__(self, item: Permission) -> bool:
        return item in self._permissions
