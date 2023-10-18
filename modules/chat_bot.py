from typing import List, NamedTuple, Union

from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import WebsocketClientConfig
from graia.ariadne.entry import config
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member, Stranger
from graia.ariadne.model.util import AriadneOptions

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

        self._is_running: bool = False

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
                    stack.extend(self._auth_manager.get_user(user_id=group.id))
                except KeyError:
                    pass

            stack.extend(
                self._auth_manager.get_user(user_id=person.id)
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
                    except KeyError:
                        # keyError is raised only when the cmd is not defined. on that account, exit will be proceeded
                        return
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

    def run(self, init_utils: bool = True) -> None:
        """
        Run the application.

        This method launches the Ariadne app in blocking mode.
        It catches a KeyboardInterrupt exception and stops the app if it is raised.
        After the app is stopped, it saves the changes made to the permissions, roles, resources, and users using the AuthManager.

        Parameters:


        Returns:
            None
        """
        self.init_utils() if init_utils else None
        if self._is_running:
            return
        try:
            self._is_running = True
            self._ariadne_app.launch_blocking()

        except KeyboardInterrupt:
            self._is_running = False
            self.stop(with_save=True)

    def stop(self, with_save: bool = True) -> None:
        """
        Stop the bot
        """
        if self._is_running:
            self._ariadne_app.stop()
            self._is_running = False
            if with_save:
                self._auth_manager.save()
                for extension in self._extensions.plugins_view.values():
                    extension.config.save_config()

    def reboot(self):
        if self._is_running:
            import subprocess
            from constant import USER_BATCH_SCRIPT_PATH

            subprocess.Popen("cls", shell=True)
            subprocess.Popen(USER_BATCH_SCRIPT_PATH, shell=True)
            exit(0)
