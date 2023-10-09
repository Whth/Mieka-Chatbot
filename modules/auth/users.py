from pydantic import validator, Field
from typing import Type, Iterable, List

from .roles import Role
from .utils import AuthBaseModel, manager_factory, ManagerBase


class User(AuthBaseModel):
    name: str
    roles: List[Role] = Field(default_factory=list, unique_items=True)

    @validator("roles")
    def validate_roles(cls, roles: Iterable[Role]) -> List[Role]:
        """
        Validate the roles input.

        Args:
            cls (Type): The class object.
            roles (Iterable[Role]): The roles to be validated.

        Returns:
            List[Role]: The validated roles as a list.

        Raises:
            ValueError: If any role in the input is not an instance of Role.
        """
        for role in roles:
            if not isinstance(role, Role):
                raise ValueError(f"Role {role} is not an instance of Role")

        return list(set(roles))

    def add_role(self, role: Role):
        """
        Adds a role to the user.

        Args:
            role (Role): The role to be added.

        Raises:
            KeyError: If the user already has the specified role.

        Returns:
            None
        """
        if role in self.roles:
            raise KeyError(f"User {self.name} already has role {role.name}")
        self.roles.append(role)

    def remove_role(self, role: Role):
        """
        Removes a role from the user.

        Args:
            role (Role): The role to be removed from the user.

        Raises:
            KeyError: If the user does not have the specified role.

        Returns:
            None
        """
        if role not in self.roles:
            raise KeyError(f"User {self.name} does not have role {role.name}")
        self.roles.remove(role)

    def __contains__(self, item: Role) -> bool:
        return item in self.roles


UserManager: Type[ManagerBase] = manager_factory(User)
