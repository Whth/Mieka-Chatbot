import pathlib
from pydantic import PrivateAttr, validator
from typing import Optional, NamedTuple, Any, Dict, Iterable, List

from .permissions import Permission, PermissionCode, PermissionManager
from .resources import ResourceManager, Resource, required_perm_generator, RequiredPermission
from .roles import RoleManager, Role
from .users import UserManager, User
from .utils import AuthBaseModel, make_label, UniqueLabel


class Root(NamedTuple):
    id: int = 0
    name: str = "root"


class AuthorizationManager(AuthBaseModel):
    class Config:
        allow_mutation = True

    __su_permission__: Permission = PrivateAttr(default=Permission(id=PermissionCode.SuperPermission.value, name="su"))

    # TODO add root user ,and add to the managers,
    # TODO remove the exception raise when re-add
    config_file_path: pathlib.Path | str
    _users: UserManager = PrivateAttr()
    _roles: RoleManager = PrivateAttr()
    _permissions: PermissionManager = PrivateAttr()
    _resources: ResourceManager = PrivateAttr()

    @validator("config_file_path")
    def validate_config_file_path(cls, path: str | pathlib.Path) -> str:
        path_obj = pathlib.Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        return str(path_obj.absolute())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = Root()._asdict()
        self._permissions = PermissionManager(**root, config_file_path=self.config_file_path)
        self._roles = RoleManager(**root, config_file_path=self.config_file_path)
        self._users = UserManager(**root, config_file_path=self.config_file_path)
        self._resources = ResourceManager(**root, config_file_path=self.config_file_path)
        self._permissions.add_object(self.__su_permission__)
        su_role = Role(**root, permissions=[self.__su_permission__])
        self._roles.add_object(su_role)
        su_user = User(id=self.id, name=self.name, roles=[su_role])
        self._users.add_object(su_user)

    def add_user(self, user_id: int, user_name: str, user_roles: Optional[Iterable[UniqueLabel]] = None) -> bool:
        try:
            if user_roles:
                user_roles: List[Role] = [self._roles.object_dict[label] for label in user_roles]
            else:
                user_roles = []
            return self._users.add_object(User(id=user_id, name=user_name, roles=user_roles))
        except KeyError:
            return False

    def remove_user(self, user_id: int, user_name: str) -> bool:
        try:
            self._users.remove_object(make_label(user_id, user_name))
            return True
        except KeyError:
            return False

    def add_role(self, role_id: int, role_name: str, role_perms: Optional[Iterable[UniqueLabel]] = None) -> bool:
        try:
            if role_perms:
                role_perms: List[Permission] = [self._permissions.object_dict[label] for label in role_perms]
            else:
                role_perms = []

            return self._roles.add_object(Role(id=role_id, name=role_name, permissions=role_perms))
        except KeyError:
            return False

    def remove_role(self, role_id: int, role_name: str) -> bool:
        try:
            self._roles.remove_object(make_label(role_id, role_name))
            return True
        except KeyError:
            return False

    def add_perm(self, perm_id: int, perm_name: str) -> bool:
        return self._permissions.add_object(Permission(id=perm_id, name=perm_name))

    def remove_perm(self, perm_id: int, perm_name: str) -> bool:
        try:
            self._permissions.remove_object(make_label(perm_id, perm_name))
            return True
        except KeyError:
            return False

    def add_resource(self, resource_id: int, resource_name: str, source: Any, std_init: bool = True) -> bool:
        """
        Adds a resource to the object's resource collection.

        Args:
            resource_id (int): The ID of the resource.
            resource_name (str): The name of the resource.
            source (Any): The source of the resource.
            std_init (bool, optional): Indicates whether to use the standard initialization.
            Defaults to True.

        Returns:
            bool: True if the resource was added successfully, False otherwise.
        """
        if std_init:
            req_perm = required_perm_generator(
                required_perm_id=resource_id,
                required_perm_name=resource_name,
                target_resource_name=resource_name,
                super_permissions=[self.__su_permission__],
            )
            req_perm_list: List[Permission] = req_perm.read + req_perm.modify + req_perm.execute + req_perm.delete
            # standard initialization will create standard access permissions, so registration is required
            for perm in req_perm_list:
                self._permissions.add_object(perm)

            return self._resources.add_object(
                Resource(id=resource_id, name=resource_name, source=source, required_permissions=req_perm)
            )
        else:
            return self._resources.add_object(
                Resource(
                    id=resource_id,
                    name=resource_name,
                    source=source,
                    required_permissions=RequiredPermission(
                        id=resource_id,
                        name=resource_name,
                        super=[self.__su_permission__],
                    ),
                )
            )

    def remove_resource(self, resource_id: int, resource_name: str) -> bool:
        try:
            self._resources.remove_object(make_label(id=resource_id, name=resource_name))
            return True
        except KeyError:
            return False

    def grant_perm_to_resource(self, perm_label: str, resource_label: str, category_name: str) -> bool:
        try:
            source: Resource = self._resources.object_dict[resource_label]
            perm_to_grant: Permission = self._permissions.object_dict[perm_label]
            source.required_permissions.add_permission(perm_to_grant, category_name)
            return True
        except KeyError:
            return False

    def grant_perm_to_role(self, perm_label: str, role_label: str) -> bool:
        try:
            self._roles.object_dict.get(role_label).add_permission(self._permissions.object_dict.get(perm_label))
            return True
        except KeyError:
            return False

    def grant_role_to_user(self, role_label: str, user_label: str) -> bool:
        try:
            self._users.object_dict.get(user_label).add_role(self._roles.object_dict.get(role_label))
            return True
        except KeyError:
            return False

    def save(self) -> None:
        self._permissions.save_object_list()
        self._roles.save_object_list()
        self._resources.save_object_list()
        self._users.save_object_list()

    def laod(self):
        self._permissions.load_object_list()
        self._roles.load_object_list()
        self._resources.load_object_list()
        self._users.load_object_list()

    def update_resources(self, source_dict: Dict[str, Any]):
        self._resources.update_sources(su_permissions=[self.__su_permission__], source_dict=source_dict)
