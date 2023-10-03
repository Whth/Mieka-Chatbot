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
    _root_key: str = PrivateAttr("root")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # use setattr here is to silent the warning, use '=' to set it is fine, too
        setattr(self, "_root_key", f"{self.ele_type.__name__}s")

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
    def save_object_list(self):
        """
        A method that is responsible for saving a list of objects.

        This method does not have any parameters.

        This method does not return any value.
        """
        pass

    @abstractmethod
    def load_object_list(self):
        """
        A description of the entire function, its parameters, and its return types.
        """
        pass


T_AUTH_BASE_MODEL = TypeVar("T_AUTH_BASE_MODEL", bound=AuthBaseModel)


def manager_factory(T_type: Type[T_AUTH_BASE_MODEL]) -> Type[ManagerBase]:
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

        def _make_json_dict(self):
            return {self._root_key: [data.dict() for data in self.object_dict.values()]}

        @override
        def save_object_list(self):
            with open(self.config_file_path, "w+", encoding="utf-8") as f:
                json.dump(self._make_json_dict(), f, indent=2, ensure_ascii=False)

        @override
        def load_object_list(self):
            with open(self.config_file_path, "r", encoding="utf-8") as f:
                temp: List[Dict] = json.load(f)[self._root_key]

            temp_object_list = [T_type(**data) for data in temp]
            for temp_object in temp_object_list:
                self.add_object(temp_object)

    return GenericManager
