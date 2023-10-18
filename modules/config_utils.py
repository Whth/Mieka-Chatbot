import inspect
import os
import re
from functools import singledispatch
from json import load, dump
from types import MappingProxyType
from typing import Any, Dict, List, Union, TypeVar
from typing import Sequence, Tuple, Optional, Callable

from colorama import Back, Fore, Style

from constant import CONFIG_PATH_PATTERN, Value


def registry_path_to_chain(config_registry_path) -> List[str]:
    """

    Args:
        config_registry_path ():

    Returns:

    """
    config_registry_path_chain: List[str] = re.split(pattern=CONFIG_PATH_PATTERN, string=config_registry_path)
    return config_registry_path_chain


def get_signature(func) -> List[str]:
    """
    Returns a list of strings representing the names of the parameters of the given function.

    Parameters:
        func (callable): The function for which to retrieve the parameter names.

    Returns:
        List[str]: A list of strings representing the names of the parameters of the given function.
    """
    sig = inspect.signature(func)
    params = [param for param in sig.parameters]
    return params


def get_signature_with_annotations(func) -> Dict[str, Any]:
    """
    Retrieves the signature of a function with its annotations.

    Args:
        func (callable): The function to retrieve the signature from.

    Returns:
        dict: A dictionary containing the parameters as keys and their corresponding annotations as values.
    """
    sig = inspect.signature(func)
    params = {}
    for param in sig.parameters.values():
        params[param.name] = param.annotation
    return params


# region get_config
@singledispatch
def get_config(body: Union[Dict, MappingProxyType], chain: Sequence[str]) -> Any:
    """
    Get config_registry recursively from the nested dict
    Args:
        body (dict): The nested dictionary
        chain (Sequence[str]): The sequence of keys representing the path to the desired value

    Returns:
        Any: The value associated with the specified chain in the nested dictionary
    """
    raise KeyError(f"The chain is conflicting, as the chain is {chain}, but the body is {body}")


@get_config.register(dict)
def _(body: Union[Dict, MappingProxyType], chain: Sequence[str]) -> Any:
    if len(chain) == 1:
        # Store the value
        return body.get(chain[0])
    else:
        return get_config(body.get(chain[0]), chain[1:])


@get_config.register(type(None))
def _() -> Any:
    return None


# endregion


# region make_config
@singledispatch
def make_config(body: Dict, chain: Sequence[str], value: Any) -> Dict:
    """
    Inject config_registry to a nested dict
    Args:
        body (dict): The nested dictionary
        chain (Sequence[str]): The sequence of keys representing the path to the desired value.
        value (Any): The value to be injected

    Returns:
        dict: The modified nested dictionary with the injected config_registry
    """
    raise KeyError("The chain is conflicting")


@make_config.register(dict)
def _(body: Dict, chain: Sequence[str], value: Any) -> Dict:
    """
    Recursive call util the chain is empty


    Args:
        body ():
        chain ():
        value ():

    Returns:

    Notes:
        Here is to deal with two different situations
        first is the situation,
        in which the body doesn't contain the key named chain[0],indicating that
        there is no existed nested Dict.
        For that here parse a None as the body,
        which prevents body[chain[0]] raising the KeyError

        Second is the situation, in which the body does contain the key named chain[0],indicating that
        there should be a nested Dict.
        For that here parse the nested Dict as the Body,
        which may contain other configurations
    """

    if len(chain) == 1:
        # Store the value
        body[chain[0]] = value
        return body
    else:
        # Recursive call until the chain is empty
        if chain[0] not in body:
            body[chain[0]] = None
        body[chain[0]] = make_config(body[chain[0]], chain[1:], value)
        return body


@make_config.register(type(None))
def _(body, chain: Sequence[str], value: Any) -> Dict:
    if len(chain) == 1:
        # Store the value
        return {chain[0]: value}
    else:
        # Recursive call until the chain is empty
        return {chain[0]: make_config(body, chain[1:], value)}


# endregion


def get_all_config_chains(body: Dict[str, Any]) -> Tuple[List[List[str]], List[Any]]:
    """
    Recursively flatten the keys of a dictionary.

    Args:
        body (Dict[str, Any]): The dictionary to flatten.


    Returns:
        List[List[str]]: The flattened keys.
    """

    all_config_chains: List[List[str]] = []
    values: List[Any] = []

    def _get_chains_recursive(
        data_body: Dict[str, Any], parent_chain: List[str], chain_container: Optional[List[List[str]]] = None
    ) -> None:
        chain_container: List[List[str]] = chain_container if chain_container is not None else []
        for key, value in data_body.items():
            current_keys: List[str] = parent_chain + [key]
            if isinstance(value, dict):
                _get_chains_recursive(value, current_keys, chain_container)
            else:
                chain_container.append(current_keys)
                values.append(value)

    _get_chains_recursive(body, [], all_config_chains)
    return all_config_chains, values


class ConfigRegistry(object):

    """
    a config_registry registry class using json
    """

    __config_registry_instance: List["ConfigRegistry"] = []

    @classmethod
    def save_all_configs(cls):
        """
        save all ConfigRegistry instance
        Returns:

        """
        config_count = len(cls.__config_registry_instance)
        print(Back.BLACK + Fore.GREEN + "Saving ConfigRegistry to json file..." + Style.RESET_ALL)
        for config_registry in cls.__config_registry_instance:
            if not config_registry.config_file_path:
                continue
            config_registry.save_config()

            print(Back.CYAN + Fore.RED + f"\rRemaining {config_count} configs to save..." + Style.RESET_ALL)
            config_count -= 1
        print(Back.BLACK + Fore.GREEN + "Done" + Style.RESET_ALL)

    def __init__(self, config_path: Optional[str] = None):
        """

        Args:
            config_path ():
        """
        self._config_file_path: str = config_path if config_path else ""
        self._config_registry_table: Dict[str, Value] = {}
        self._config_registry_table_proxy: MappingProxyType[str, Value] = MappingProxyType(self._config_registry_table)

        self.__config_registry_instance.append(self)

    @property
    def config_file_path(self) -> str:
        """
        the path where stores the config_registry file, in json format
        Returns:

        """
        return self._config_file_path

    @config_file_path.setter
    def config_file_path(self, config_path: str) -> None:
        """
        set the config_registry file path, with parent directory check
        Args:
            config_path ():


        """
        if not os.path.exists(os.path.dirname(config_path)):
            os.makedirs(os.path.dirname(config_path))
        self._config_file_path = config_path

    def load_config(self):
        """
        load config_registry
        Returns:

        """
        self._load_config(self._config_file_path)

    def _load_config(self, config_path: str):
        """
        Load the configuration from the given config_registry file path.

        Args:
            config_path (Str): The path to the config_registry file.

        Returns:

        """

        if not os.path.exists(config_path) or os.path.getsize(config_path) == 0:
            return
        with open(config_path, mode="r", encoding="utf-8") as f:
            temp = load(f)
        for key in self._config_registry_table.keys():
            config = get_config(temp, registry_path_to_chain(key))
            if config is None:
                continue
            self._config_registry_table[key] = config

    def save_config(self):
        """
        save config_registry to file
        Returns:

        """
        if not self._config_file_path:
            raise ValueError("config_registry file path is not set!")
        temp = {}
        for k, v in self._config_registry_table_proxy.items():
            make_config(temp, registry_path_to_chain(k), v)
        with open(self._config_file_path, mode="w+", encoding="utf-8") as f:
            dump(temp, f, indent=2, ensure_ascii=False)

    @property
    def registered_configs(self) -> Tuple[str]:
        """
        registry path for every configuration
        Returns:

        """
        return tuple(self._config_registry_table.keys())

    def register_config(self, registry_path: str, default_value: Value) -> None:
        """
        register config_registry
        Args:
            registry_path ():
            default_value ():

        Returns:

        """
        if registry_path in self._config_registry_table.keys():
            raise ValueError(f"{registry_path} already registered")
        self._config_registry_table[registry_path] = default_value

    def get_config(self, config_path: str) -> Value:
        """

        Args:
            config_path ():

        Returns:

        """
        if config_path not in self._config_registry_table.keys():
            raise KeyError(f"{config_path} not registered")
        return self._config_registry_table.get(config_path)

    def set_config(self, config_path: str, new_config_value: Value) -> None:
        """
        Sets a new configuration value for the given registry path in the config_registry registry table.

        Parameters:
            - registry_path (str): The path of the registry to set the new value for.
            - new_config_value (Value): The new value to set for the registry.

        Returns:
            None

        Raises:
            KeyError: If the registry path does not exist in the config_registry registry table.
        """
        if config_path not in self._config_registry_table.keys():
            raise KeyError(f"{config_path} not exists!")
        self._config_registry_table[config_path] = new_config_value


Setter = Callable[[...], None]
Void = Callable[[], None]
StringMaker = Callable[[], str]

ConfigValue = TypeVar("ConfigValue", int, str, float, list, dict)
