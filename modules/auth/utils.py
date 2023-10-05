import json
import pathlib
import warnings
from abc import abstractmethod
from pydantic import BaseModel, PositiveInt, validator, Field, PrivateAttr
from typing import TypeVar, Type, Dict, List, final, Any
from typing_extensions import override


class AuthBaseModel(BaseModel):
    id: PositiveInt

    name: str = Field(regex="^[a-zA-Z_]+$")

    @property
    def unique_label(self) -> str:
        return f"{self.id}-{self.name}"

    @final
    def __hash__(self):
        return hash((self.id, self.name))

    @final
    def __eq__(self, other) -> bool:
        return self.id == other.id and self.name == other.name

    @final
    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    class Config:
        allow_mutation = False
        validate_assignment = True


class ManagerBase(AuthBaseModel):
    ele_type: Type
    config_file_path: pathlib.Path | str
    object_dict: Dict[str, Any]
    load_on_init: bool = True
    _root_key: str = PrivateAttr("root")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.ele_type is None:
            raise ValueError("ele_type cannot be None")
        # use setattr here is to silent the warning, use '=' to set it is fine, too
        setattr(self, "_root_key", f"{self.ele_type.__name__}s")
        self.load_object_list() if pathlib.Path(self.config_file_path).exists() and self.load_on_init else None

    @property
    def root_key(self) -> str:
        return self._root_key

    @validator("config_file_path")
    def validate_user_config_file_path(cls, path: pathlib.Path | str) -> str:
        """
        Validates the user-configured file path.

        Args:
            cls: The class object.
            path (Union[pathlib.Path, str]): The path to the configuration file.

        Returns:
            pathlib.Path: The validated path to the configuration file.
        """
        path = pathlib.Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())

    @final
    def add_object(self, new_object: AuthBaseModel) -> bool:
        """
        Adds a new object to the object list if it is not already present.

        Args:
            new_object (AuthBaseModel): The object to be added to the list.

        Returns:
            bool: True if the object is added successfully, False if the object is already present in the list.
        """
        if new_object.unique_label in self.object_dict:
            warnings.warn(
                f"[<{new_object.id}>-{new_object.name}] is already in the object list, skipping",
                category=UserWarning,
                stacklevel=1,
            )
            return False
        self.object_dict[new_object.unique_label] = new_object
        return True

    @final
    def remove_object(self, target: AuthBaseModel):
        """
        Remove an object from the object list.

        Parameters:
            target (AuthBaseModel): The object to be removed from the list.

        Raises:
            KeyError: If the target object is not in the object list.

        Returns:
            None
        """
        if target.unique_label not in self.object_dict:
            raise KeyError(f"[<{target.id}>-{target.name}] is not in the object list")
        del self.object_dict[target.unique_label]

    @abstractmethod
    def _make_json_dict(self) -> Dict:
        """
        A method that should be implemented by subclasses. It is responsible for creating a JSON dictionary.

        :return: A dictionary representing the JSON data.
        :rtype: Dict
        """
        pass

    @final
    def save_object_list(self):
        """
        Save the object list to a JSON file.

        This function reads the existing JSON file, if it exists, and loads its contents into a temporary
        dictionary.
        It then updates the dictionary with the contents of the object list by calling the
        _make_json_dict() method.
        Finally, it writes the updated dictionary to the JSON file, overwriting its
        previous contents.

        Parameters:


        Returns:
            None
        """
        temp = {}
        if pathlib.Path(self.config_file_path).exists():
            with open(self.config_file_path, "r", encoding="utf-8") as f:
                temp = json.load(f)
        temp.update(self._make_json_dict())
        with open(self.config_file_path, "w+", encoding="utf-8") as f:
            json.dump(temp, f, indent=2, ensure_ascii=False)

    @abstractmethod
    def _make_object_instance(self, **kwargs) -> AuthBaseModel:
        """
        Creates an instance of `AuthBaseModel` with the provided keyword arguments.

        Parameters:
            **kwargs: Additional keyword arguments to be passed to the constructor of `AuthBaseModel`.

        Returns:
            AuthBaseModel: An instance of `AuthBaseModel` with the specified keyword arguments.
        """
        pass

    @final
    def load_object_list(self):
        """
        Load the object list from the config file.

        This function opens the config file specified by `config_file_path` in read mode,
        and loads the object list from it. The object list is stored under the `_root_key` key
        in the JSON file.

        Parameters:
            self (ClassName): The instance of the class.

        Returns:
            None
        """
        with open(self.config_file_path, "r", encoding="utf-8") as f:
            temp: List[Dict] = json.load(f)[self._root_key]

        temp_object_list = [self._make_object_instance(**data) for data in temp]
        for temp_object in temp_object_list:
            self.add_object(temp_object)


T_AUTH_BASE_MODEL = TypeVar("T_AUTH_BASE_MODEL", bound=AuthBaseModel)

T_Manager = TypeVar("T_Manager", bound=ManagerBase)


def manager_factory(T_type: Type[T_AUTH_BASE_MODEL]) -> Type[T_Manager]:
    """
    Returns a dynamically generated manager class based on the provided type.

    Parameters:
        T_type (Type[T_AUTH_BASE_MODEL]): The type of the base model for the manager class.

    Returns:
        Type[ManagerBase]: The dynamically generated manager class.
    """

    class GenericManager(ManagerBase):
        ele_type: Type = Field(default=T_type, exclude=True, const=True)
        object_dict: Dict[str, T_type] = Field(default_factory=dict, const=True)

        @override
        def _make_json_dict(self) -> Dict:
            return {self._root_key: [object_instance.dict() for object_instance in self.object_dict.values()]}

        @override
        def _make_object_instance(self, **kwargs) -> T_type:
            return T_type(**kwargs)

    return GenericManager
