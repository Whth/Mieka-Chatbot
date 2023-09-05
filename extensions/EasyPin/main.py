import os
import random
import re
from typing import Dict

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.base import ContainKeyword
from graia.ariadne.model import Group, Friend

from modules.plugin_base import AbstractPlugin

__all__ = ["EasyPin"]


class EasyPin(AbstractPlugin):
    __PIN_TASK_SET_CMD_REGEX = r"set task"
    __PIN_TASK_DELETE_CMD_REGEX = r"delete task"
    __PIN_TASK_LIST_CMD_REGEX = r"list task"

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
        self._config_registry.register_config(self.CONFIG_DETECTED_KEYWORD, "#pin")

    def install(self):
        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        bord_cast = ariadne_app.broadcast
        task_registry: Dict = {}

        task_types: Dict = {}

        from graia.scheduler import GraiaScheduler, timers

        scheduler = self._ariadne_app.create(GraiaScheduler)

        @bord_cast.receiver(
            ["GroupMessage", "FriendMessage"],
            decorators=[ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD))],
        )
        async def add_new_task(group: Group, friend: Friend, chain: MessageChain):
            async def task():
                pass
                # TODO implement task

            extract_crontab = re.findall(self.__PIN_TASK_SET_CMD_REGEX, str(chain))
            task_wrapper = scheduler.schedule(timers.crontabify(f"{extract_crontab} * 0"))
            wrapped_task = task_wrapper(task)
            task_registry[extract_crontab] = wrapped_task

        @bord_cast.receiver(
            ["GroupMessage", "FriendMessage"],
            decorators=[ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD))],
        )
        async def list_all_tasks(group: Group, friend: Friend, chain: MessageChain):
            print(task_registry)

        @bord_cast.receiver(
            ["GroupMessage", "FriendMessage"],
            decorators=[ContainKeyword(keyword=self._config_registry.get_config(self.CONFIG_DETECTED_KEYWORD))],
        )
        async def delete_task():
            pass


def get_random_file(folder):
    """

    :param folder:
    :return:
    """
    from modules.file_manager import explore_folder

    files_list = explore_folder(folder)
    return random.choice(files_list)
