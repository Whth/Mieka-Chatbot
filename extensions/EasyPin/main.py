import os
import re

from modules.plugin_base import AbstractPlugin

__all__ = ["EasyPin"]


class EasyPin(AbstractPlugin):
    __TASK_CMD = "task"
    __TASK_SET_CMD = "new"
    __TASK_LIST_CMD = "list"
    __TASK_DELETE_CMD = "delete"
    __TASK_CLEAN_CMD = "clean"
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
        return "a simple notify application"

    @classmethod
    def get_plugin_version(cls) -> str:
        return "0.0.2"

    @classmethod
    def get_plugin_author(cls) -> str:
        return "whth"

    def __register_all_config(self):
        self._config_registry.register_config(
            self.CONFIG_TASKS_SAVE_PATH, f"{self._get_config_parent_dir()}/cache/tasks.json"
        )

    def install(self):
        from graia.scheduler import GraiaScheduler
        from graia.scheduler.timers import crontabify
        from graia.broadcast import Broadcast
        from graia.ariadne.event.message import GroupMessage
        from graia.ariadne.event.lifecycle import ApplicationLaunch
        from graia.ariadne.message.parser.base import ContainKeyword

        from graia.ariadne.model import Group
        from .analyze import Preprocessor, DEFAULT_PRESET, TO_DATETIME_PRESET, DATETIME_TO_CRONTAB_PRESET
        from .task import TaskRegistry, ReminderTask, T_TASK

        self.__register_all_config()
        self._config_registry.load_config()
        ariadne_app = self._ariadne_app
        broad_cast: Broadcast = ariadne_app.broadcast
        scheduler: GraiaScheduler = self._ariadne_app.create(GraiaScheduler)
        to_datetime_processor = Preprocessor(TO_DATETIME_PRESET)
        datetime_to_crontab_processor = Preprocessor(DATETIME_TO_CRONTAB_PRESET)
        full_processor = Preprocessor(DEFAULT_PRESET)
        task_registry = TaskRegistry(self._config_registry.get_config(self.CONFIG_TASKS_SAVE_PATH), ReminderTask)

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
            stdout = "\n\n".join(f"{cmd} {help_string}" for cmd, help_string in zip(cmds, help_strings))
            return stdout

        def _task_list() -> str:
            task_registry.remove_outdated_tasks()
            temp_string = "Task List:\n"
            for crontab, tasks in task_registry.tasks.items():
                for name, _task in tasks.items():
                    _task: T_TASK
                    temp_string += f"{_task.task_name} | {_task.crontab}\n"
            return temp_string

        def _clean() -> str:
            clean_task_ct = 0
            for scheduled_task in scheduler.schedule_tasks:
                if not scheduled_task.stopped:
                    scheduled_task.stop()
                    scheduled_task.stop_gen_interval()
                    clean_task_ct += 1
            task_registry.remove_all_task()
            return f"Cleaned {clean_task_ct} Tasks in total"

        tree = {
            self.__TASK_CMD: {
                self.__TASK_HELP_CMD: _help,
                # self.__TASK_SET_CMD: None,
                self.__TASK_CLEAN_CMD: _clean,
                self.__TASK_LIST_CMD: _task_list,
                self.__TASK_DELETE_CMD: None,
                self.__TASK_TEST_CMD: _test_convert,
            }
        }

        self._cmd_client.register(tree, True)

        @broad_cast.receiver(GroupMessage, decorators=[ContainKeyword(self.__TASK_CMD)])
        async def pin_opreator(group: Group, message: GroupMessage):
            # Define the pattern for matching the command and arguments
            pat = rf"{self.__TASK_CMD}\s+{self.__TASK_SET_CMD}\s+(\S+)(?:\s+(.+)|(?:\s+)?$)"

            # Check if the message has an origin attribute
            if not hasattr(message.quote, "origin"):
                print("no origin, not accepted")
                return

            # Compile the regular expression pattern
            comp = re.compile(pat)

            # Find all matches of the pattern in the message
            matches = re.findall(comp, str(message.message_chain))

            # If no matches are found, return
            if not matches:
                print("reg matches not accepted")
                return

            # Get the first match group
            match_groups = matches[0]

            # Get the origin id from the message quote
            origin_id = message.quote.id

            # Process the match group and add "0" at the end
            crontab = full_processor.process(match_groups[0], True) + " 0"

            # Create a new ReminderTask object
            task = ReminderTask(
                crontab=crontab,
                remind_content=[origin_id],
                target=group.id,
                task_name=match_groups[1] if match_groups[1] else None,
            )

            # Register the task in the task registry
            task_registry.register_task(task=task)

            # Save the tasks in the task registry
            task_registry.save_tasks()

            # Send a message to the group with the details of the scheduled task
            await ariadne_app.send_message(group, f"Schedule new task:\n {task.task_name} | {crontab}")

            # Schedule the task using the scheduler
            scheduler.schedule(crontabify(crontab), cancelable=True)(
                await task.make(ariadne_app),
            )

            # Run the last scheduled task
            await scheduler.schedule_tasks[-1].run()

        @broad_cast.receiver(ApplicationLaunch)
        async def fetch_tasks():
            from colorama import Fore

            print(f"{Fore.YELLOW}Fetching tasks{Fore.RESET}")
            for task in task_registry.task_list:
                # Schedule the task using the scheduler
                scheduler.schedule(crontabify(task.crontab), cancelable=True)(
                    await task.make(ariadne_app),
                )

                # Run the last scheduled task
                await scheduler.schedule_tasks[-1].run()
