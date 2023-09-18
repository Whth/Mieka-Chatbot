import os
import re
from functools import singledispatch
from inspect import signature
from json import load, dump
from types import MappingProxyType
from typing import Any, Dict, List, Union, TypeVar, Type
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


import inspect


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
    Get config recursively from the nested dict
    Args:
        body (dict): The nested dictionary
        chain (Sequence[str]): The sequence of keys representing the path to the desired value

    Returns:
        Any: The value associated with the specified chain in the nested dictionary
    """
    raise KeyError("The chain is conflicting")


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
        the path where stores the config file, in json format
        Returns:

        """
        return self._config_file_path

    @config_file_path.setter
    def config_file_path(self, config_path: str) -> None:
        """
        set the config file path, with parent directory check
        Args:
            config_path ():


        """
        if not os.path.exists(os.path.dirname(config_path)):
            os.makedirs(os.path.dirname(config_path))
        self._config_file_path = config_path

    def load_config(self):
        """
        load config
        Returns:

        """
        self._load_config(self._config_file_path)

    def _load_config(self, config_path: str):
        """
        Load the configuration from the given config file path.

        Args:
            config_path (Str): The path to the config file.

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
        save config to file
        Returns:

        """
        if not self._config_file_path:
            raise ValueError("config file path is not set!")
        temp = {}
        for k, v in self._config_registry_table_proxy.items():
            make_config(temp, registry_path_to_chain(k), v)
        with open(self._config_file_path, mode="w+") as f:
            dump(temp, f, indent=2)

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
        Sets a new configuration value for the given registry path in the config registry table.

        Parameters:
            - registry_path (str): The path of the registry to set the new value for.
            - new_config_value (Value): The new value to set for the registry.

        Returns:
            None

        Raises:
            KeyError: If the registry path does not exist in the config registry table.
        """
        if config_path not in self._config_registry_table.keys():
            raise KeyError(f"{config_path} not exists!")
        self._config_registry_table[config_path] = new_config_value


Setter = Callable[[...], None]
Void = Callable[[], None]
StringMaker = Callable[[], str]


class CmdClient(object):
    """
    a config client that allows simple cli-liked operation on config
    """

    def __init__(self, syntax_tree: Optional[Dict[str, Any]] = None):
        self._Hall_Cmd_Tree: Dict[str, Any] = {}
        self.Hall_Cmd_Tree: MappingProxyType = MappingProxyType(self._Hall_Cmd_Tree)
        self.register(syntax_tree) if syntax_tree else None

    @property
    def get_all_available_cmd(self) -> Tuple[str]:
        """
        Returns a list of all available commands.

        :return: A list of strings representing the available commands.
        :rtype: List[str]
        """

        return tuple(self._Hall_Cmd_Tree.keys())

    def get_help(self, cmd_path_chain: List[str]) -> Union[List[str], Dict[str, Any]]:
        """
        Retrieves the help information for a command specified by the given command path chain.

        Parameters:
            cmd_path_chain (List[str]): A list of strings representing the path to the desired command.

        Returns:
            Union[List[str], Dict[str, Any]]: The help information for the command.
            If the command is callable, return the signature with annotations.
            If the command is a dictionary, returns a list of its keys.
        """
        cmd_options = get_config(self.Hall_Cmd_Tree, cmd_path_chain)
        if callable(cmd_options):
            return get_signature_with_annotations(cmd_options)
        if isinstance(cmd_options, Dict):
            return list(cmd_options.keys())

    def interpret(self, cmd: str) -> Any:
        """
        Interprets a command and executes it.

        Args:
            cmd: The command to interpret.

        Returns:
            The result of executing the command.

        Raises:
            KeyError: If the command is not supported or has an incorrect number
                of arguments.
        """
        # Split the command into tokens
        cmd_tokens: List[str] = re.split(r"\s+", cmd)
        tokens_count = len(cmd_tokens)
        temp: Union[Dict, MappingProxyType, Setter, Void, StringMaker] = self.Hall_Cmd_Tree

        # Traverse the syntax tree based on command tokens
        for token in cmd_tokens:
            if token not in temp:
                return

            temp = temp[token]
            tokens_count -= 1

            # If a callable is encountered, execute it
            if callable(temp):
                # Extract the parameter names from the function signature
                hints = signature(temp).parameters
                params_name_list: List[str] = list(hints.keys())
                required_token_count = len(hints)

                # If the number of tokens matches the number of parameters
                if tokens_count == required_token_count:
                    raw_params = cmd_tokens[-tokens_count:]

                    # Convert the raw parameters to their annotated types
                    params_pack = tuple(
                        hints[param_name].annotation(raw_param)
                        for param_name, raw_param in zip(params_name_list, raw_params)
                    )

                    return temp(*params_pack)
                else:
                    raise ValueError(f"expected {required_token_count} args, got {tokens_count}")

        raise KeyError("Bad syntax tree, please check")

    def register(self, syntax_tree: Dict[str, Any]):
        """
        Register a new syntax tree for a command.

        Parameters:
            syntax_tree (Dict[str, Any]): The syntax tree to register.

        Raises:
            KeyError: If the command is already registered.

        Returns:
            None
        """
        if any(key in self.Hall_Cmd_Tree for key in syntax_tree.keys()):
            raise KeyError("cmd already registered!")
        self._Hall_Cmd_Tree.update(syntax_tree)


ConfigValue = TypeVar("ConfigValue", int, str, float, list, dict)


class CmdBuilder(object):
    """
    build the cmd functions for a specific config client
    """

    def __init__(self, config_getter: Callable[[str], Value], config_setter: Callable[[str, Value], None]):
        self._config_setter = config_setter
        self._config_getter = config_getter

    def build_setter_for(self, config_path: str) -> Callable[[str], str]:
        """
        Returns a callable function that can be used to set a configuration value.

        Args:
            config_path (str): The path to the configuration value.

        Returns:
            Callable[[str], str]: A callable function that takes in a new configuration value as a string and returns a string message indicating the success or failure of the operation.
        """

        origin_config = self._config_getter(config_path)
        origin_config_type = type(origin_config)

        def _setter(new_config: str) -> str:
            try:
                converted = origin_config_type(new_config)
            except ValueError as e:
                return f"Can not set [{config_path}] to [{new_config}]\nERROR:\n\t[{e}]"
            self._config_setter(config_path, converted)
            return f"Set [{config_path}]:\nFrom [{origin_config}] to [{new_config}]"

        _setter(origin_config)  # test if it works
        return _setter

    def build_setter_hall(self) -> Callable[[str, str], str]:
        """
        Builds and returns a setter function that can be used to modify configuration values.


        Returns:
            str: A message indicating the result of the configuration modification.
        """

        def _setter(config_path: str, new_config: str) -> str:
            """
            Sets the value of a configuration option.

            Args:
                config_path (str): The path of the configuration option.
                new_config (str): The new value to set.

            Returns:
                str: A message indicating the success or failure of the operation.
            """
            origin_config = self._config_getter(config_path)

            origin_config_type: Type = type(origin_config)

            try:
                converted = origin_config_type(new_config)
            except ValueError as e:
                return f"Can not set [{config_path}] to [{new_config}]\nERROR:\n\t[{e}]"
            self._config_setter(config_path, converted)
            return f"Set [{config_path}]:\nFrom [{origin_config}] to [{new_config}]"

        return _setter

    def build_list_out_for(self, config_paths: List[str]) -> Callable[[], str]:
        """
        Builds and returns a function that lists out the values of the given config paths.

        Parameters:
            config_paths (List[str]): A list of config paths.

        Returns:
            Callable[[], str]: A function that, when called, returns a string listing out the values of the config paths.
        """

        def _list_out() -> str:
            temp_string: str = ""
            for config_path in config_paths:
                temp_string += f"{config_path} = {self._config_getter(config_path)}\n"
            return temp_string

        _list_out()  # test if it works
        return _list_out
