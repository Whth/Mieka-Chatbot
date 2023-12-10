import re
from abc import abstractmethod
from inspect import iscoroutinefunction
from typing import Dict, Any, List, Union, Callable, Type, Unpack, final, TypeVar, Iterable, Awaitable, TypeAlias, Set

from pydantic import BaseModel, Field, root_validator, validator

from constant import Value
from modules.auth import Permission, auth_check, RequiredPermission
from modules.config_utils import (
    get_signature_with_annotations,
)
from modules.file_manager import generate_random_string


def tokenize_cmd(cmd: str) -> List[str]:
    """
    Tokenizes a command string.

    Args:
        cmd (str): The command string to tokenize.

    Returns:
        List[str]: The list of tokens extracted from the command string.
    """
    # Remove leading and trailing whitespace
    cmd = cmd.strip()

    # Find all substrings enclosed in double quotes
    sub_pat = re.compile(r'("[^"]*")')
    matched: List[str] = sub_pat.findall(cmd)

    # Replace matched substrings with random tokens
    repl_tokens_table: Dict[str, str] = {}
    for match in matched:
        repl_token: str = generate_random_string(10)
        cmd = cmd.replace(match, repl_token)
        repl_tokens_table[repl_token] = match.strip('"')

    # Split the command string into tokens
    split_cmd: List[str] = re.split(r"\s+", cmd)

    # Replace random tokens with their original substrings
    final_tokens: List[str] = []
    for token in split_cmd:
        final_tokens.append(repl_tokens_table[token] if token in repl_tokens_table else token)

    return final_tokens


def make_stdout_seq_string(seq: Iterable[Any], title: str = "", extra: str = "") -> str:
    """
    Generates a formatted string representation of a sequence, with an optional title and extra information.

    Args:
        seq (Iterable[Any]): The sequence to be converted to a string.
        title (str, optional): An optional title for the string representation. Defaults to "".
        extra (str, optional): Any extra information to be appended to the string representation. Defaults to "".

    Returns:
        str: The formatted string representation of the sequence.

    Example:
        >>> seq = [1, 2, 3]
        >>> make_stdout_seq_string(seq, title="Numbers", extra="Total count: 3")
        'Numbers\n----------------\n[0]: 1\n[1]: 2\n[2]: 3\n\nTotal count: 3'
    """
    output = ""
    if title:
        output += f"{title}\n----------------\n"

    output += "\n".join(f"[{i}]: {s}" for i, s in enumerate(seq))

    if extra:
        output += f"\n----------------\n\n{extra}"
    return output


class CmdBuilder(object):
    """
    build the cmd functions for a specific config_registry client
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
        Builds and returns a function that lists out the values of the given config_registry paths.

        Parameters:
            config_paths (List[str]): A list of config_registry paths.

        Returns: Callable[[], str]: A function that, when called, returns a string listing out the values of the
        config_registry paths.
        """

        def _list_out() -> str:
            temp_string: str = ""
            for config_path in config_paths:
                temp_string += f"{config_path} = {self._config_getter(config_path)}\n"
            return temp_string

        _list_out()  # test if it works
        return _list_out


__su_permissions__: List[Permission] = []


def set_su_permissions(permissions: Iterable[Permission]) -> None:
    """
    Set superuser permissions.

    This function overrides the existing permissions with the given permissions.
    The set value will be used to namespace access check, allowing all operations for
    NameSpaceNode and ExecutableNode with any of the permissions in the list.

    Args:
        permissions: An iterable of Permission objects.

    Raises:
        TypeError: If any of the permissions is not of type Permission.

    Returns:
        None
    """
    global __su_permissions__

    if all(isinstance(perm, Permission) for perm in permissions):
        __su_permissions__ = list(permissions)
    else:
        raise TypeError("All permissions must be of type Permission")


class BaseCmdNode(BaseModel):
    class Config:
        allow_mutation = False
        validate_assignment = True
        validate_all = True

    name: str = Field(min_length=1)

    aliases: List[str] = Field(default_factory=set, unique_items=True)
    help_message: str = Field(default="no help provided")
    required_permissions: RequiredPermission = Field(default_factory=RequiredPermission)

    @root_validator
    def name_and_aliases(cls, values) -> Dict[str, Any]:
        """
        Validates the 'name_and_aliases' field in the input values dictionary.

        Parameters:
            cls (Type): The class of the model being validated.
            values (Dict[str, Any]): The input values dictionary.

        Returns:
            Dict[str, Any]: The validated values' dictionary.

        Raises:
            ValueError: If the name and aliases are the same.
        """
        if values["name"] in values["aliases"]:
            raise ValueError(
                f"Name and aliases must be different. Name: {values['name']}, Aliases: {values['aliases']}"
            )

        return values

    @validator("aliases")
    def validate_aliases(cls, aliases: List[str]) -> List[str]:
        """
        Validates a list of aliases.

        Args:
            cls (type): The class that the validator is attached to.
            aliases (List[str]): The list of aliases to validate.

        Returns:
            List[str]: The validated list of aliases.

        Raises:
            ValueError: If any alias in the list is an empty string.
        """
        if any(len(alias) == 0 for alias in aliases):
            raise ValueError("Aliases must not be empty strings")
        return aliases

    @final
    def __eq__(self, other) -> bool:
        return self.name == other.name

    @final
    def __ne__(self, other) -> bool:
        return self.name != other.name

    @final
    def __str__(self) -> str:
        return self.name

    @abstractmethod
    def __doc__(self) -> str:
        return self.help_message

    def get_read(self, permissions: Iterable[Permission]) -> Any:
        global __su_permissions__
        if auth_check(
            self.required_permissions.read,
            permissions,
            optional_super=__su_permissions__ + self.required_permissions.super,
        ):
            return self._read()
        raise PermissionError("Illegal Read operation, insufficient permissions")

    @abstractmethod
    def _read(self) -> Any:
        pass

    def get_modify(self, permissions: Iterable[Permission], *modify_params: Unpack) -> Any:
        global __su_permissions__
        if auth_check(
            self.required_permissions.modify,
            permissions,
            optional_super=__su_permissions__ + self.required_permissions.super,
        ):
            return self._modify(*modify_params)
        raise PermissionError("Illegal Modify operation, insufficient permissions")

    @abstractmethod
    def _modify(self, *modify_params: Unpack) -> Any:
        pass

    def get_delete(self, permissions: Iterable[Permission], *delete_params: Unpack) -> Any:
        global __su_permissions__
        if auth_check(
            self.required_permissions.delete,
            permissions,
            optional_super=__su_permissions__ + self.required_permissions.super,
        ):
            return self._delete(*delete_params)
        raise PermissionError("Illegal Delete operation, insufficient permissions")

    @abstractmethod
    def _delete(self, *delete_params: Unpack) -> Any:
        pass

    async def get_execute(self, permissions: Iterable[Permission], *execute_params: Unpack) -> Any:
        global __su_permissions__
        if auth_check(
            self.required_permissions.execute,
            permissions,
            optional_super=__su_permissions__ + self.required_permissions.super,
        ):
            return await self._execute(*execute_params)
        raise PermissionError("Illegal Execute operation, insufficient permissions")

    @abstractmethod
    async def _execute(self, *execute_params: Unpack) -> Any:
        pass


T_CmdNode: TypeAlias = TypeVar("T_CmdNode", bound=BaseCmdNode)


class ExecutableNode(BaseCmdNode):
    source: Union[Callable, None] = Field(default=None, allow_mutation=True, exclude=True, validate_assignment=True)

    def _modify(self, *modify_params: Unpack) -> Any:
        if len(modify_params) == 1:
            if callable(modify_params[0]):
                setattr(self, "source", modify_params[0])

        else:
            raise ValueError("too many arguments, accepted 1")

    def _delete(self) -> Any:
        setattr(self, "source", None)

    async def _execute(self, *execute_params: Unpack) -> Any:
        sig = get_signature_with_annotations(self.source)
        converted = []
        for para, param_type in zip(execute_params, sig.values()):
            try:
                # try to convert it to the right type
                converted.append(param_type(para))
            except TypeError:
                # if the force conversion fails, use the original value
                converted.append(para)

        return await self.source(*converted) if iscoroutinefunction(self.source) else self.source(*converted)

    def _read(self) -> Any:
        return self.source.__name__

    def __doc__(self) -> str:
        output = f"{self.name:<10}|{self.aliases}\n\n"

        output += f"{self.source.__doc__}\n\n"
        if self.help_message != self.source.__doc__:
            output += self.help_message

        return output


class NameSpaceNode(BaseCmdNode):
    children_node: List[T_CmdNode] = Field(default_factory=list, unique_items=True, validate_assignment=True)

    @validator("children_node")
    def validate_children_node(cls, children_node: List[T_CmdNode]) -> List[T_CmdNode]:
        """
        Validates the `children_node` parameter of the `validate_children_node` function.

        Parameters:
            cls (Type): The class of the `validate_children_node` function.
            children_node (List[T_CmdNode]): The list of `T_CmdNode` objects to be validated.

        Returns:
            List[T_CmdNode]: The validated list of `T_CmdNode` objects.

        Raises:
            ValueError: If the aliases in the `children_node` are not unique.

        """
        collide_group = has_identifier_collision(children_node)
        if collide_group:
            raise ValueError(
                f"Under, Aliases must be unique,check node under to find duplicates\n"
                f"{make_stdout_seq_string(collide_group)}"
            )
        return children_node

    def __doc__(self) -> str:
        nodes = [f"{child.name:<10}|{child.aliases}" for child in self.children_node]
        return make_stdout_seq_string(nodes, title=f"{self.name:<10}|{self.aliases}", extra=self.help_message)

    def _read(self) -> Any:
        return self

    def _modify(self, *modify_params: Unpack) -> Any:
        merge_queue = []
        for param in modify_params:
            if isinstance(param, list):
                merge_queue.extend(param)
                continue
            merge_queue.append(param)

        self.children_node.extend(filter(lambda x: isinstance(x, (ExecutableNode, NameSpaceNode)), merge_queue))

    def _delete(self, *delete_params: Unpack) -> Any:
        self.children_node.clear()

    async def _execute(self, *execute_params: Unpack) -> Any:
        raise NotImplementedError(f"{self.name} does not support execute operation")

    def get_node(
        self,
        chain: List[str],
        permissions: Iterable[Permission] = tuple(),
    ) -> Union["NameSpaceNode", "ExecutableNode"]:
        """
        Get the node with the specified chain of names.

        Args:
            chain (List[str]): The chain of names to traverse to find the target node.
            permissions (List[Permission]): The list of permissions for the user.

        Returns:
            Union[NameSpaceNode, ExecutableNode]: The target node with the specified chain of names.

        Raises:
            PermissionError: If the user does not have sufficient permissions.
            KeyError: If the chain is empty or if no node with the specified name is found.
        """
        global __su_permissions__
        if not auth_check(
            self.required_permissions.read,
            permissions,
            optional_super=__su_permissions__ + self.required_permissions.super,
        ):
            raise PermissionError("Illegal Read operation, insufficient permissions")
        # Check if the chain is empty
        if len(chain) == 0:
            raise KeyError("The chain is empty")

        # Filter the children nodes to find the target node with the first name in the chain
        target_node: List[Union["NameSpaceNode", "ExecutableNode"]] = list(
            filter(lambda x: x.name == chain[0] or chain[0] in x.aliases, self.children_node)
        )

        # Check if multiple nodes with the same name are found
        if len(target_node) > 1:
            raise KeyError(
                f"Multiple nodes with name {chain[0]} found,see below\n{make_stdout_seq_string(target_node)}"
            )
        # Check if a single node is found
        elif len(target_node) == 1:
            # If there are more names in the chain, recursively call get_node on the target node
            if len(chain) > 1:
                return target_node[0].get_node(chain[1:], permissions)
            # If there are no more names in the chain, return the target node
            elif len(chain) == 1:
                return target_node[0]

        # If no node is found in the chain, raise an exception
        raise KeyError(f"No node with name {chain[0]} found")

    def add_node(
        self,
        node: Union["NameSpaceNode", "ExecutableNode"],
        permissions: List[Permission] = tuple(),
    ) -> None:
        """
        Adds a node to the current object.

        Args:
            node (Union[NameSpaceNode, ExecutableNode]): The node object to be added.
            permissions (List[Permission], optional): The permissions required to add the node.
                Defaults to an empty list.


        Raises:
            PermissionError: If the user does not have the required permissions to add the node.
            TypeError: If the node is not of type NameSpaceNode or ExecutableNode.
            KeyError: If a node with the same name already exists.

        Returns:
            None: This function does not return any value.
        """
        global __su_permissions__
        if auth_check(
            self.required_permissions.modify,
            permissions,
            optional_super=__su_permissions__ + self.required_permissions.super,
        ):
            if not isinstance(node, (NameSpaceNode, ExecutableNode)):
                raise TypeError(f"Node must be of type {NameSpaceNode} or {ExecutableNode}")
            if node not in self.children_node:
                self.children_node.append(node)
                if has_identifier_collision(self.children_node):
                    self.children_node.pop()
                    raise KeyError(f"Node with name {node.name} already exists")
                return
            raise KeyError(f"Node with name {node.name} already exists")
        raise PermissionError("Illegal Modify operation, insufficient permissions")

    def remove_node(
        self,
        node: Union["NameSpaceNode", "ExecutableNode", str, List[str]],
        permissions: Iterable[Permission] = tuple(),
    ) -> None:
        """
        Remove a node from the namespace.

        Args:
            node (Union["NameSpaceNode", "ExecutableNode", str, List[str]]): The node to be removed.
                It can be an instance of NameSpaceNode, ExecutableNode, a string representing the name of the node,
                or a list of strings representing the path to the node.

            permissions (List[Permission], optional): The permissions required to remove it.
                Defaults to an empty list.

        Raises:
            PermissionError: If the user does not have the required permissions to perform the delete operation.

        Returns:
            None
        """
        global __su_permissions__
        if any(su_perm in permissions for su_perm in __su_permissions__ + self.required_permissions.super) or (
            auth_check(self.required_permissions.delete, permissions)
            and auth_check(self.required_permissions.read, permissions)
        ):
            if isinstance(node, str):
                node = self.get_node([node], permissions)
            elif isinstance(node, list):
                parent_node = self.get_node(node[:-1], permissions)
                parent_node.remove_node(node[-1], permissions)
                return

            if node not in self.children_node:
                raise KeyError(f"Node with name {node.name} does not exist")
            self.children_node.remove(node)
            return
        raise PermissionError(
            "Illegal Delete operation, insufficient permissions, you need have the read and delete permissions"
        )

    async def interpret(
        self, string: str, permissions: Iterable[Permission] = tuple(), documentation_keyword: str = "doc"
    ) -> str | Awaitable[Any]:
        """
        Asynchronously interprets a command string and executes the corresponding command.

        Parameters:
            string (str): The command string to be interpreted.
            permissions (Iterable[Permission], optional): The permissions required to execute the command.
                    Default to an empty tuple.
            documentation_keyword (str, optional): The keyword to retrieve documentation.
                    Defaults to "doc".

        Returns:
            Any: The result of executing the command.

        Raises:
            KeyError: If the command string is empty.

        Note:
            - This function tokenizes the command string into individual tokens.
            - It iterates through the tokens to find the corresponding command node.
            - If the command node is an `ExecutableNode`, it executes the command.
            - If the command node is a `NameSpaceNode`, it returns the documentation of the node.

        """

        # Tokenize the command string, these tokens could contain cmds and parameters
        tokens = tokenize_cmd(string)

        # Check if there are no tokens
        if len(tokens) == 0:
            raise KeyError("Empty command")

        target_node = None
        # Iterate through the tokens
        for i in range(1, len(tokens) + 1):
            # this is to verify the parameter token counts
            # Get the corresponding node for the current tokens
            target_node = self.get_node(tokens[:i], permissions)

            # If the node is an ExecutableNode, execute the command
            if isinstance(target_node, ExecutableNode):
                args = tokens[i:]
                if len(args) == 1 and args[0] == documentation_keyword:
                    # return the documentation
                    return target_node.__doc__()
                return target_node.get_execute(permissions, *args)

        # If the node is a NameSpaceNode, return its documentation
        if isinstance(target_node, NameSpaceNode):
            # TODO doc access is not a permission restricted-option, shall give it one?
            return target_node.__doc__()


def has_identifier_collision(children_node: List[T_CmdNode]) -> List[T_CmdNode]:
    """
    Check if there are any identifier collisions among the given list of command nodes.

    Parameters:
        children_node (List[T_CmdNode]): A list of command nodes.

    Returns:
        List[T_CmdNode]: A list of command nodes that have identifier collisions.
    """
    aliases_seq: List[str] = []
    aliases_set: Set[str] = set()
    for i, child in enumerate(children_node, start=1):
        aliases_seq.extend(child.aliases)
        aliases_seq.append(child.name)
        aliases_set.update(child.aliases)
        aliases_set.add(child.name)
        if len(aliases_seq) != len(aliases_set):
            return children_node[:i]
    return []
