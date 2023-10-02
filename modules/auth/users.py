from typing import Set, Optional, FrozenSet

from modules.auth.roles import Role


class User(object):
    def __init__(self, user_id, username, roles: Optional[Set[Role]] = None):
        self._user_id = user_id
        self._username = username
        self._roles: Set[Role] = roles if roles else set()

    @property
    def id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def roles(self) -> FrozenSet[Role]:
        return frozenset(self._roles)

    def add_role(self, role: Role):
        self._roles.add(role)

    def remove_role(self, role: Role):
        if role not in self._roles:
            raise KeyError(f"User {self._username} does not have role {role}")
        self._roles.remove(role)

    def __contains__(self, item: Role) -> bool:
        return item in self._roles
