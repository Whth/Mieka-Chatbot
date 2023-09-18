import os
from typing import Union

from modules.plugin_base import AbstractPlugin

__all__ = ["EasyPin"]


class EasyPin(AbstractPlugin):
    __TASK_CMD = "task"
    __TASK_SET_CMD = "set"
    __TASK_LIST_CMD = "list"
    __TASK_DELETE_CMD = "delete"

    def _get_config_parent_dir(self) -> str:
        return os.path.abspath(os.path.dirname(__file__))

    @classmethod
    def get_plugin_name(cls) -> str:
        return "EasyPin"

    @classmethod
    def get_plugin_description(cls) -> str:
        return "EasyPin"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.1"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        pass

    def install(self):
        from graia.scheduler import GraiaScheduler
        from graia.broadcast import Broadcast
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.model import Group, Friend
        from graia.ariadne.event.message import MessageEvent
        from graia.ariadne.message.parser.base import ContainKeyword
        from modules.config_utils import CmdClient

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        broad_cast: Broadcast = ariadne_app.broadcast
        scheduler: GraiaScheduler = self._ariadne_app.create(GraiaScheduler)

        tree = {self.__TASK_CMD: {self.__TASK_SET_CMD: None, self.__TASK_LIST_CMD: None, self.__TASK_DELETE_CMD: None}}

        self._cmd_client.register(tree)

        cmd_infer_tree={
            "后":{},
            "明":{},
            "今":{},
            "下":{},
            "本":{},
            "周":{}

        }
        interpret_tree = {}
        interpreter = CmdClient(interpret_tree)

        @broad_cast.receiver(MessageEvent, decorators=[ContainKeyword(self.__TASK_CMD)])
        async def pin_opreator(sender: Union[Group, Friend], message: MessageChain):


