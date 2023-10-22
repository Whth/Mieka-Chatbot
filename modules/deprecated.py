import warnings
from inspect import signature, iscoroutinefunction
from types import MappingProxyType
from typing import Optional, Dict, Any, Tuple, List, Union

from modules.cmd import tokenize_cmd
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
    a config_registry client that allows simple cli-liked operation on config_registry
    """

    # TODO should add a override lock to avoid concurrent access
    def __init__(self, syntax_tree: Optional[Dict[str, Any]] = None):
        self._Hall_Cmd_Tree: Dict[str, Any] = {}
        self.Hall_Cmd_Tree: MappingProxyType = MappingProxyType(self._Hall_Cmd_Tree)
        self.register(syntax_tree, True) if syntax_tree else None
        warnings.warn("CmdClient is deprecated", category=DeprecationWarning)

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
        cmd_tokens: List[str] = tokenize_cmd(cmd)
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
