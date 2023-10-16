from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import WebsocketClientConfig
from graia.ariadne.entry import config
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member, Stranger
from graia.ariadne.model.util import AriadneOptions
from typing import List, NamedTuple, Union

from modules.auth.core import AuthorizationManager, Root
from modules.auth.roles import Role
from modules.auth.users import User
from modules.cmd import NameSpaceNode, set_su_permissions
from modules.extension_manager import ExtensionManager
from modules.plugin_base import PluginsView


class BotInfo(NamedTuple):
    """
    Represents information about a bot.

    Attributes:
        account_id (int): The ID of the bot account.
        bot_name (str, optional): The name of the bot. Default to an empty string.
    """

    account_id: int
    bot_name: str = ""


class BotConnectionConfig(NamedTuple):
    """
    Represents the connection configuration for a bot.

    Attributes:
        verify_key (str): The verification key for the connection.
        websocket_config (WebsocketClientConfig, optional): The configuration for the WebSocket client.
        Default to WebsocketClientConfig().
    """

    verify_key: str
    websocket_config: WebsocketClientConfig = WebsocketClientConfig()


class BotConfig(NamedTuple):
    """
    Configuration settings for the bot.

    Attributes:
        extension_dir (str): The directory path for the bot extensions.
        auth_config_file_path (str): The file path for the authentication configuration.
        accepted_message_types (List[str], optional): The list of accepted message types.
            Defaults to ["GroupMessage"].
    """

    extension_dir: str
    auth_config_file_path: str
    accepted_message_types: List[str] = ["GroupMessage"]


class ChatBot(object):
    """
    ChatBot class
    """

    @property
    def root(self) -> NameSpaceNode:
        """
        Returns the root node of the NameSpace tree.

        :return: The root node of the NameSpace tree.
        :rtype: NameSpaceNode
        """
        return self._root

    @property
    def extensions(self) -> ExtensionManager:
        """
        Returns the ExtensionManager object that manages the extensions for this class.

        :return: An instance of the ExtensionManager class.
        :rtype: ExtensionManager
        """
        return self._extensions

    @property
    def auth_manager(self) -> AuthorizationManager:
        """
        Return the authorization manager object.

        :return: An instance of AuthorizationManager.
        :rtype: AuthorizationManager
        """
        return self._auth_manager

    def __init__(self, bot_info: BotInfo, bot_config: BotConfig, bot_connection_config: BotConnectionConfig):
        self._ariadne_app: Ariadne = Ariadne(
            config(bot_info.account_id, bot_connection_config.verify_key, bot_connection_config.websocket_config)
        )
        Ariadne.options = AriadneOptions(default_account=bot_info.account_id)
        self._bot_name: str = bot_info.bot_name
        self._bot_config: BotConfig = bot_config

        self._auth_manager: AuthorizationManager = AuthorizationManager(
            **(Root()._asdict()), config_file_path=bot_config.auth_config_file_path
        )

        set_su_permissions([self._auth_manager.__su_permission__])
        self._root: NameSpaceNode = NameSpaceNode(name="root")
        self._extensions: ExtensionManager = ExtensionManager(self._bot_config.extension_dir, [])

        for message_type in bot_config.accepted_message_types:
            self._ariadne_app.broadcast.receiver(message_type)(self._make_cmd_interpreter())

    def _make_cmd_interpreter(self):
        async def _cmd_interpret(person: Union[Friend, Member], message: MessageChain):
            """
            Asynchronously calls the bot client with the given target and message.

            Args:
                person (Union[Friend, Member, Stranger]): The target of the bot client call.
                message (MessageChain): The message to be sent.

            Returns:
                None

            Raises:
                KeyError: If the user is not found.
            """
            stack: List[User] = []
            group = None
            if isinstance(person, Member):
                group = person.group

                try:
                    stack.append(self._auth_manager.get_user(user_id=group.id, user_name=group.name))
                except KeyError:
                    pass

            stack.append(
                self._auth_manager.get_user(
                    user_id=person.id, user_name=person.name if isinstance(person, Member) else person.nickname
                )
            )  # if this fails, then there is no need to go further

            success = False
            roles_bunch: List[List[Role]] = [user.roles for user in stack]
            owned_roles: List[Role] = []
            for role in roles_bunch:
                owned_roles.extend(role)
            for role in owned_roles:
                with role as perms:
                    try:
                        stdout = await self._root.interpret(str(message), perms)
                        success = True
                    except PermissionError:
                        pass
                if success:
                    break

            target = group if group else person
            (await self._ariadne_app.send_message(target, message=stdout)) if stdout else None

        return _cmd_interpret

    @property
    def get_installed_plugins(self) -> PluginsView:
        """
        Installed plugins
        Returns:

        """
        return self._extensions.plugins_view

    def init_utils(self) -> None:
        """
        Initializes the utils for the class.

        Args:
            self: The instance of the class.

        Returns:
            None.
        """
        self._extensions.install_all_requirements()
        self._extensions.install_all_extensions(
            broadcast=self._ariadne_app.broadcast,
            root_namespace_node=self._root,
            proxy=self._extensions.plugins_view,
            auth_manager=self._auth_manager,
        )
        # TODO better add a hall perm checker, to eliminate unregistered perm be used

    def run(self) -> None:
        """
        Runs the function.

        This function is responsible for executing the main logic of the program.
        It performs the following steps:

        1. Install all the requirements by calling `install_all_requirements()` with the `extension_dir` parameter.
        2. Install all the extensions by calling `install_all_extensions()` with the `extension_dir` parameter.
        3. Retrieve the `Broadcast` object from the `_ariadne_app` attribute.
        4. Posts an `AllExtensionsInstalledEvent()` event to the broadcast.
        5. Launches the `_ariadne_app` in blocking mode.

        If a `KeyboardInterrupt` exception is raised during the execution, the function will call `stop()`
        to stop the program.

        Parameters:


        Returns:
            None
        """

        try:
            self._ariadne_app.launch_blocking()

        except KeyboardInterrupt:
            self.stop()
        finally:
            print("Save the changes made to the permissions, roles, resources, and users.")
            self._auth_manager.save()

    def stop(self) -> None:
        """
        Stop the bot
        """
        self._ariadne_app.stop()
