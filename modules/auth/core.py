import inspect
import pathlib
from functools import wraps
from pydantic import PrivateAttr, validator
from typing import Optional, NamedTuple, Any, Dict, Iterable, List, Callable, Type

from .permissions import Permission, PermissionCode, PermissionManager
from .resources import ResourceManager, Resource, required_perm_generator, RequiredPermission
from .roles import RoleManager, Role
from .users import UserManager, User
from .utils import AuthBaseModel, make_label, UniqueLabel


class Root(NamedTuple):
    id: int = 0
    name: str = "root"


def final_handler(final_method: str, exception: Optional[Type[Exception]] = Exception) -> Callable:
    """
    Decorator that wraps a function and handles exceptions and a final method call.

    Args:
        final_method (str): The name of the final method to be called after the function is executed.
        exception (Optional[Type[Exception]], optional): The type of exception to catch. Defaults to Exception.

    Returns:
        Callable: The wrapped function.

    """

    def decorator(func):
        """
        Decorates a function with the given decorator.

        Parameters:
            func (function): The function to be decorated.

        Returns:
            function: The decorated function.

        Raises:
            exception: If an exception occurs during the execution of the decorated function.

        """
        sig = inspect.signature(func)
        if sig.return_annotation != bool:
            raise ValueError("The return annotation of the decorated function must be bool.")

        @wraps(func)
        def wrapped(self, *args, **kwargs) -> bool:
            result = False
            try:
                result = func(self, *args, **kwargs)
            except exception:
                pass
            finally:
                final_method_obj = getattr(self, final_method)
                final_method_obj()
            return result

        return wrapped  # 更新装饰函数的元信息

    return decorator


class AuthorizationManager(AuthBaseModel):
    class Config:
        allow_mutation = True

    __su_permission__: Permission = PrivateAttr(default=Permission(id=PermissionCode.SuperPermission.value, name="su"))

    config_file_path: pathlib.Path | str
    _users: UserManager = PrivateAttr()
    _roles: RoleManager = PrivateAttr()
    _permissions: PermissionManager = PrivateAttr()
    _resources: ResourceManager = PrivateAttr()

    @property
    def users(self) -> List[User]:
        return list(self._users.object_dict.values())

    @property
    def roles(self) -> List[Role]:
        return list(self._roles.object_dict.values())

    @property
    def permissions(self) -> List[Permission]:
        return list(self._permissions.object_dict.values())

    @property
    def resources(self) -> List[Resource]:
        return list(self._resources.object_dict.values())

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
        self.load()
        su_role = Role(**root, permissions=[self.__su_permission__])
        self._roles.add_object(su_role)
        su_user = User(id=self.id, name=self.name, roles=[su_role])
        self._users.add_object(su_user)

    @final_handler("save", KeyError)
    def add_user(self, user_id: int, user_name: str, user_roles: Optional[Iterable[UniqueLabel]] = None) -> bool:
        """
        Adds a user to the system.

        Args:
            user_id (int): The ID of the user.
            user_name (str): The name of the user.
            user_roles (Optional[Iterable[UniqueLabel]]): The roles of the user. Defaults to None.

        Returns:
            bool: True if the user was added successfully, False otherwise.
        """
        if user_roles:
            user_roles: List[Role] = [self._roles.object_dict[label] for label in user_roles]
        else:
            user_roles = []
        return self._users.add_object(User(id=user_id, name=user_name, roles=user_roles))

    @final_handler("save", KeyError)
    def remove_user(self, user_id: int, user_name: str) -> bool:
        """
        Removes a user from the list of users.

        Parameters:
            user_id (int): The ID of the user to be removed.
            user_name (str): The name of the user to be removed.

        Returns:
            bool: True if the user was successfully removed, False otherwise.
        """
        self._users.remove_object(make_label(user_id, user_name))
        return True

    def get_user(self, user_id: Optional[int] = None, user_name: Optional[str] = None) -> User | List[User]:
        if user_id and user_name:
            return self._users.object_dict[make_label(user_id, user_name)]
        elif user_id:
            return list(filter(lambda user: user.id == user_id, self._users.object_dict.values()))
        elif user_name:
            return list(filter(lambda user: user.name == user_name, self._users.object_dict.values()))
        else:
            raise KeyError("Either user_id or user_name must be provided.")

    @final_handler("save", KeyError)
    def add_role(self, role_id: int, role_name: str, role_perms: Optional[Iterable[UniqueLabel]] = None) -> bool:
        """
        Adds a role to the RoleManager.

        Parameters:
            role_id (int): The ID of the role.
            role_name (str): The name of the role.
            role_perms (Optional[Iterable[UniqueLabel]]): The permissions of the role. Defaults to None.

        Returns:
            bool: True if the role was successfully added, False otherwise.
        """
        if role_perms:
            role_perms: List[Permission] = [self._permissions.object_dict[label] for label in role_perms]
        else:
            role_perms = []

        return self._roles.add_object(Role(id=role_id, name=role_name, permissions=role_perms))

    @final_handler("save", KeyError)
    def remove_role(self, role_id: int, role_name: str) -> bool:
        """
        Remove a role from the list of roles.

        Parameters:
            role_id (int): The ID of the role to be removed.
            role_name (str): The name of the role to be removed.

        Returns:
            bool: True if the role was successfully removed, False otherwise.
        """
        self._roles.remove_object(make_label(role_id, role_name))
        return True

    @final_handler("save", KeyError)
    def add_perm_from_info(self, perm_id: int, perm_name: str) -> bool:
        """
        Adds a permission to the object.

        Args:
            perm_id (int): The ID of the permission.
            perm_name (str): The name of the permission.

        Returns:
            bool: True if the permission was successfully added, False otherwise.
        """
        return self._permissions.add_object(Permission(id=perm_id, name=perm_name))

    @final_handler("save", KeyError)
    def add_perm_from_raw(self, perm: Permission) -> bool:
        """
        Adds a permission to the object.
        """
        return self._permissions.add_object(perm)

    @final_handler("save", KeyError)
    def add_perm_from_req(self, required_permission: RequiredPermission) -> bool:
        """
        Adds a permission to the object.
        """

        return all(
            self._permissions.add_object(perm)
            for perm in required_permission.read
            + required_permission.modify
            + required_permission.execute
            + required_permission.delete
            + required_permission.super
        )

    @final_handler("save", KeyError)
    def remove_perm(self, perm_id: int, perm_name: str) -> bool:
        """
        Removes a permission from the object.

        Args:
            perm_id (int): The ID of the permission to be removed.
            perm_name (str): The name of the permission to be removed.

        Returns:
            bool: True if the permission was successfully removed, False otherwise.
        """
        self._permissions.remove_object(make_label(perm_id, perm_name))
        return True

    @final_handler("save", KeyError)
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
                        super=[self.__su_permission__],
                    ),
                )
            )

    @final_handler("save", KeyError)
    def remove_resource(self, resource_id: int, resource_name: str) -> bool:
        """
        Remove a resource from the list of resources.

        Args:
            resource_id (int): The ID of the resource to be removed.
            resource_name (str): The name of the resource to be removed.

        Returns:
            bool: True if the resource was successfully removed, False otherwise.
        """
        self._resources.remove_object(make_label(id=resource_id, name=resource_name))
        return True

    @final_handler("save", KeyError)
    def grant_perm_to_resource(self, perm_label: str, resource_label: str, category_name: str) -> bool:
        """
        Grant permission to a resource.

        Args:
            perm_label (str): The label of the permission to grant.
            resource_label (str): The label of the resource to grant permission to.
            category_name (str): The name of the category to associate with the granted permission.

        Returns:
            bool: True if the permission was successfully granted, False otherwise.
        """
        source: Resource = self._resources.object_dict[resource_label]
        perm_to_grant: Permission = self._permissions.object_dict[perm_label]
        source.required_permissions.add_permission(perm_to_grant, category_name)
        return True

    @final_handler("save", KeyError)
    def grant_perm_to_role(self, perm_label: str, role_label: str) -> bool:
        """
        Grant permission to a role.

        Args:
            perm_label (str): The label of the permission to grant.
            role_label (str): The label of the role to grant the permission to.

        Returns:
            bool: True if the permission was granted successfully, False otherwise.
        """
        self._roles.object_dict.get(role_label).add_permission(self._permissions.object_dict.get(perm_label))
        return True

    @final_handler("save", KeyError)
    def grant_role_to_user(self, role_label: str, user_label: str) -> bool:
        """
        Grant a role to a user.

        Args:
            role_label (str): The label of the role to be granted.
            user_label (str): The label of the user to grant the role to.

        Returns:
            bool: True if the role is successfully granted to the user, False otherwise.
        """
        self._users.object_dict.get(user_label).add_role(self._roles.object_dict.get(role_label))
        return True

    def save(self) -> None:
        """
        Save the changes made to the permissions, roles, resources, and users.

        Returns:
            None
        """
        self._permissions.save_object_list()
        self._roles.save_object_list()
        self._resources.save_object_list()
        self._users.save_object_list()

    def load(self):
        """
        Load the object lists for permissions, roles, resources, and users.

        This function loads the object lists for permissions, roles, resources, and users.
        It does not take any parameters and does not return any values.

        Returns:
            None
        """
        if not pathlib.Path(self.config_file_path).exists():
            return
        self._permissions.load_object_list()
        self._roles.load_object_list()
        self._resources.load_object_list()
        self._users.load_object_list()

    def update_resources(self, source_dict: Dict[str, Any]):
        """
        Updates the resources with the given source dictionary.

        Args:
            source_dict (Dict[str, Any]):
            A dictionary containing the source information to update the resources with.

        Returns:
            None

        Raises:
            None
        """
        self._resources.update_sources(su_permissions=[self.__su_permission__], source_dict=source_dict)
