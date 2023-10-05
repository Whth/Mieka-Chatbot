import pathlib
from pydantic import PrivateAttr, Field, PositiveInt, validator
from typing import List, Optional, NamedTuple, Any, Dict

from .permissions import Permission, PermissionCode, PermissionManager
from .resources import ResourceManager
from .roles import RoleManager
from .users import UserManager
from .utils import AuthBaseModel


class Root(NamedTuple):
    id: int = 0
    name: str = "root"


class AuthorizationManager(AuthBaseModel):
    class Config:
        allow_mutation = True

    id: PositiveInt = Field(default=Root.id, exclude=True, const=True, allow_mutation=False)
    name: str = Field(default=Root.name, regex="^[a-zA-Z_]+$", exclude=True, const=True, allow_mutation=False)
    __su_permission__: Permission = PrivateAttr(default=Permission(id=PermissionCode.Super.value, name="su"))

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

    def add_user(self, user_id: int, user_name: str) -> bool:
        pass

    def remove_user(self, user_id: int, user_name: str) -> bool:
        pass

    def add_role(self, role_id: int, role_name: str, perms: Optional[List[Permission]]) -> bool:
        pass

    def remove_role(self, role_id: int, role_name: str) -> bool:
        pass

    def add_perm(self, perm_id: int, perm_name: str) -> bool:
        pass

    def remove_perm(self, perm_id: int, perm_name: str) -> bool:
        pass

    def add_resource(self, resource_id: int, resource_name: str, std_init: bool = True) -> bool:
        pass

    def remove_resource(self, resource_id: int, resource_name: str) -> bool:
        pass

    def save(self) -> None:
        self._permissions.save_object_list()
        self._roles.save_object_list()
        self._resources.save_object_list()
        self._users.save_object_list()

    def update_resources(self, source_dict: Dict[str, Any]):
        self._resources.update_sources(su_permissions=[self.__su_permission__], source_dict=source_dict)
