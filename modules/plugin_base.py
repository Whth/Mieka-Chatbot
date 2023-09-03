import os.path
import re
from abc import ABC, abstractmethod
from functools import singledispatch
from json import load, dump
from types import MappingProxyType
from typing import final, Dict, List, Union, Sequence, Any, Tuple

from graia.ariadne import Ariadne

Value = Union[str, int, float, List, Dict]
CONFIG_PATH_PATTERN = r"[\\/]"


def registry_path_to_chain(config_registry_path) -> List[str]:
    """

    Args:
        config_registry_path ():

    Returns:

    """
    config_registry_path_chain: List[str] = re.split(
        pattern=CONFIG_PATH_PATTERN, string=config_registry_path
    )
    return config_registry_path_chain


# region get_config
@singledispatch
def get_config(body: Dict, chain: Sequence[str]) -> Any:
    """
    Get config recursively from the nested dict
    Args:
        body (dict): The nested dictionary
        chain (Sequence[str]): The sequence of keys representing the path to the desired value

    Returns:
        Any: The value associated with the specified chain in the nested dictionary
    """
    raise KeyError("The chain is conflicting")


@get_config.register(dict)
def _(body: Dict, chain: Sequence[str]) -> Any:
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
    Inject config to a nested dict
    Args:
        body (dict): The nested dictionary
        chain (Sequence[str]): The sequence of keys representing the path to the desired value.
        value (Any): The value to be injected

    Returns:
        dict: The modified nested dictionary with the injected config
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


class ConfigRegistry(object):
    """
    a config registry class using json
    """

    def __init__(self, config_path: str):
        """

        Args:
            config_path ():
        """
        self._config_file_path: str = config_path
        self._config_registry_table: Dict[str, Value] = {}
        self._config_registry_table_proxy: MappingProxyType[
            str, Value
        ] = MappingProxyType(self._config_registry_table)

    def _load_config(self, config_path: str):
        """
        Load the configuration from the given config file path.

        Args:
            config_path (Str): The path to the config file.

        Returns:

        """

        if not os.path.exists(config_path):
            return
        with open(config_path, mode="r") as f:
            temp = load(f)
        for key in self._config_registry_table.keys():
            self._config_registry_table[key] = get_config(
                temp, registry_path_to_chain(key)
            )

    def save_config(self):
        """
        save config to file
        Returns:

        """
        temp = {}
        for k, v in self._config_registry_table_proxy.items():
            make_config(temp, k, v)
        with open(self._config_file_path, mode="w+") as f:
            dump(temp, f)

    @property
    def registered_configs(self) -> Tuple[str]:
        """
        registry path for every configuration
        Returns:

        """
        return tuple(self._config_registry_table.keys())

    def register_config(self, registry_path: str, default_value: Value) -> None:
        """
        register config
        Args:
            registry_path ():
            default_value ():

        Returns:

        """
        if registry_path in self._config_registry_table.keys():
            raise ValueError(f"{registry_path} already registered")
        self._config_registry_table[registry_path] = default_value

    def get_config(self, registry_path: str) -> Value:
        """

        Args:
            registry_path ():

        Returns:

        """
        if registry_path not in self._config_registry_table.keys():
            raise ValueError(f"{registry_path} not registered")
        return self._config_registry_table.get(registry_path)


class AbstractPlugin(ABC):
    """
    Abstract plugin class
    """

    @final
    def __init__(
        self,
        ariadne_app: Ariadne,
        plugins_viewer: MappingProxyType[str, "AbstractPlugin"],
    ):
        self._ariadne_app: Ariadne = ariadne_app
        self._plugin_view: MappingProxyType[str, AbstractPlugin] = plugins_viewer

    @classmethod
    @abstractmethod
    def get_plugin_name(cls) -> str:
        """
        Get the plugin name
        :return:
        :rtype:
        """
        pass

    @classmethod
    @abstractmethod
    def get_plugin_description(cls) -> str:
        """
        Get the plugin description
        :return:
        :rtype:
        """
        pass

    @classmethod
    @abstractmethod
    def get_plugin_version(cls) -> str:
        """
        Get the plugin version
        :return:
        :rtype:
        """
        pass

    @classmethod
    @abstractmethod
    def get_plugin_author(cls) -> str:
        """
        Get the plugin author
        :return:
        :rtype:
        """
        pass

    @abstractmethod
    def install(self):
        """
        Install the plugin
        """
        pass
