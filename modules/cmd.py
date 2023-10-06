import re
from inspect import signature, iscoroutinefunction
from types import MappingProxyType
from typing import Optional, Dict, Any, Tuple, List, Union, Callable, Type

from constant import Value
from modules.config_utils import (
    get_config,
    get_signature_with_annotations,
    Setter,
    Void,
    StringMaker,
    get_all_config_chains,
    make_config,
)


class CmdClient(object):
    """
    a config client that allows simple cli-liked operation on config
    """

    # TODO should add a override lock to avoid concurrent access
    def __init__(self, syntax_tree: Optional[Dict[str, Any]] = None):
        self._Hall_Cmd_Tree: Dict[str, Any] = {}
        self.Hall_Cmd_Tree: MappingProxyType = MappingProxyType(self._Hall_Cmd_Tree)
        self.register(syntax_tree, True) if syntax_tree else None

    @property
    def get_all_available_cmd(self) -> Tuple[str]:
        """
        Returns a list of all available commands.

        :return: A list of strings representing the available commands.
        :rtype: List[str]
        """

        return tuple(self.Hall_Cmd_Tree.keys())

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

    async def interpret(self, cmd: str) -> Any:
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
                    if iscoroutinefunction(temp):
                        return await temp(*params_pack)
                    return temp(*params_pack)
                else:
                    raise ValueError(f"expected {required_token_count} args, got {tokens_count}")

        raise KeyError("Bad syntax tree, please check")

    def register(self, syntax_tree: Dict[str, Any], logging: bool = True) -> None:
        """Register a new syntax tree for a command.

        Parameters:
            logging ():
            syntax_tree (Dict[str, Any]): The syntax tree to register.

        Raises:
            KeyError: If the command is already registered.

        Returns:
            None
        """

        chains, values = get_all_config_chains(syntax_tree)
        print("\n".join(f"{chain}={value}" for chain, value in zip(chains, values))) if logging else None
        for chain, value in zip(chains, values):
            make_config(self._Hall_Cmd_Tree, chain, value)


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

        Returns: Callable[[str], str]: A callable function that takes in a new configuration value as a string and
        returns a string message indicating the success or failure of the operation.
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
