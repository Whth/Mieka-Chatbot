import json
import pathlib
import re
import warnings
from abc import abstractmethod
from typing import TypeVar, Type, Dict, List, final, Any, TypeAlias, Tuple

from pydantic import BaseModel, validator, Field, PrivateAttr, NonNegativeInt

label_pattern = re.compile(r"^(\d+)-([a-zA-Z_]+)$")


def make_label(target_id: int, target_name: str) -> str:
    """
    Generate a label by combining the target ID and target name.

    Args:
        target_id (int): The ID of the target.
        target_name (str): The name of the target.

    Returns:
        str: The generated label combining the target ID and target name.
    """
    return f"{target_id}-{target_name}"


def extract_label(label: str) -> Tuple[int, str]:
    """
    Extracts a label by matching it against a label pattern.

    Args:
        label (str): The label to be extracted.

    Returns:
        Tuple[int, str]: A tuple containing the extracted label's integer value and the remaining part of the label.

    Raises:
        ValueError: If the label is invalid.

    """
    match = label_pattern.match(label)
    if match:
        return int(match[1]), match[2]
    raise ValueError(f"Invalid label: {label}")


UniqueLabel: TypeAlias = str


class AuthBaseModel(BaseModel):
    id: NonNegativeInt

    name: str = Field(regex="^[a-zA-Z_]+$")

    @property
    def unique_label(self) -> UniqueLabel:
        return make_label(self.id, self.name)

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
    def add_object(self, new_object: AuthBaseModel, info: bool = False) -> bool:
        """
        Adds a new object to the object dictionary.

        Args:
            new_object (AuthBaseModel): The new object to be added.
            info (bool, optional): Whether or not to display a warning if the object already exists.
                Defaults to False.

        Returns:
            bool: True if the object was successfully added, False otherwise.
        """
        if new_object.unique_label in self.object_dict:
            if info:
                warnings.warn(
                    f"[<{new_object.id}>-{new_object.name}] is already in the object list, skipping",
                    category=UserWarning,
                    stacklevel=1,
                )
            return False
        self.object_dict[new_object.unique_label] = new_object
        return True

    @final
    def remove_object(self, target: AuthBaseModel | str):
        """
        Remove an object from the object list.

        Parameters:
            target (AuthBaseModel): The object to be removed from the list.

        Raises:
            KeyError: If the target object is not in the object list.

        Returns:
            None
        """
        if isinstance(target, str):
            label = target
        elif isinstance(target, AuthBaseModel):
            label = target.unique_label
        else:
            raise TypeError("target must be str or AuthBaseModel")
        if label not in self.object_dict:
            raise KeyError(f"[{label}] is not in the object list")
        del self.object_dict[label]

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
            read = json.load(f)
        if self._root_key not in read:
            # root key not found in the JSON file,indicate that the object list is empty
            return
        temp: List[Dict] = read[self._root_key]

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

        def _make_json_dict(self) -> Dict:
            return {self._root_key: [object_instance.dict() for object_instance in self.object_dict.values()]}

        def _make_object_instance(self, **kwargs) -> T_type:
            return T_type(**kwargs)

    return GenericManager
