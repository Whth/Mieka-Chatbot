import os
from typing import Union

from modules.plugin_base import AbstractPlugin

__all__ = ["EasyPin"]


class EasyPin(AbstractPlugin):
    __TASK_CMD = "task"
    __TASK_SET_CMD = "set"
    __TASK_LIST_CMD = "list"
    __TASK_DELETE_CMD = "delete"
    __TASK_TEST_CMD = "abd"
    __TASK_HELP_CMD = "help"

    CONFIG_TASKS_SAVE_PATH = "tasks_save_path"

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
        self._config_registry.register_config(
            self.CONFIG_TASKS_SAVE_PATH, f"{self._get_config_parent_dir()}/cache/tasks.pkl"
        )

    def install(self):
        from graia.scheduler import GraiaScheduler
        from graia.scheduler.timers import crontabify
        from graia.broadcast import Broadcast
        from graia.ariadne.model import Group, Friend
        from graia.ariadne.event.message import MessageEvent
        from graia.ariadne.message.parser.base import ContainKeyword

        from .analyze import Preprocessor, DEFAULT_PRESET, TO_DATETIME_PRESET, DATETIME_TO_CRONTAB_PRESET
        from .task import TaskRegistry

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        broad_cast: Broadcast = ariadne_app.broadcast
        scheduler: GraiaScheduler = self._ariadne_app.create(GraiaScheduler)
        to_datetime_processor = Preprocessor(TO_DATETIME_PRESET)
        datetime_to_crontab_processor = Preprocessor(DATETIME_TO_CRONTAB_PRESET)
        full_processor = Preprocessor(DEFAULT_PRESET)
        task_registry = TaskRegistry(self._config_registry.get_config(self.CONFIG_TASKS_SAVE_PATH))

        def _test_convert(string: str) -> str:
            return to_datetime_processor.process(string)

        def _help() -> str:
            cmds = [
                self.__TASK_SET_CMD,
                self.__TASK_LIST_CMD,
                self.__TASK_DELETE_CMD,
                self.__TASK_TEST_CMD,
                self.__TASK_HELP_CMD,
            ]
            help_strings = ["用于设置任务，第一个参数为执行时间，第二个参数为任务名称，任务内容由引用的消息决定", "列举出所有的定时任务", "删除指定的任务", "时间字符串解释测试", "展示这条信息"]
            stdout = "\n".join(f"{cmd} {help_string}" for cmd, help_string in zip(cmds, help_strings))
            return stdout

        tree = {
            self.__TASK_CMD: {
                self.__TASK_HELP_CMD: _help,
                self.__TASK_SET_CMD: None,
                self.__TASK_LIST_CMD: None,
                self.__TASK_DELETE_CMD: None,
                self.__TASK_TEST_CMD: _test_convert,
            }
        }

        self._cmd_client.register(tree, True)

        @broad_cast.receiver(MessageEvent, decorators=[ContainKeyword(self.__TASK_CMD)])
        async def pin_opreator(sender: Union[Group, Friend], message: MessageEvent):
            cmd_tokens = str(message.message_chain)

            def make_task(time_string: str, task_content: str):
                async def _task():
                    pass

            scheduler.schedule(crontabify(full_processor.process(time_string) + " *"), cancelable=True)(_task)
