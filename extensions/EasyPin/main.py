import os
from typing import Dict

from modules.plugin_base import AbstractPlugin

__all__ = ["EasyPin"]


class EasyPin(AbstractPlugin):
    __TASK_CMD = "task"
    __TASK_SET_CMD = "set"
    __TASK_LIST_CMD = "list"
    __TASK_DELETE_CMD = "delete"

    CONFIG_DETECTED_KEYWORD = "detected_keyword"

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
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "pin")

    def install(self):
        from graia.scheduler import GraiaScheduler
        from graia.broadcast import Broadcast
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.message.parser.base import DetectPrefix
        from graia.ariadne.model import Group, Friend

        from modules.config_utils import ConfigClient

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast: Broadcast = ariadne_app.broadcast
        task_registry: Dict = {}

        task_types: Dict = {}

        cmd_syntax_tree: Dict = {
            self.__TASK_CMD: {
                self.__TASK_SET_CMD: None,
                self.__TASK_DELETE_CMD: None,
                self.__TASK_LIST_CMD: None,
            },
        }
        client = ConfigClient(cmd_syntax_tree)
        scheduler = self._ariadne_app.create(GraiaScheduler)

        @bord_cast.receiver(
            "GroupMessage",
            decorators=[DetectPrefix(prefix=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD))],
        )
        async def task_client(group: Group, friend: Friend, chain: MessageChain):
            async def task():
                pass
                # TODO implement task
