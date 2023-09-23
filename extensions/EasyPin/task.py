import datetime
import json
import pathlib
from abc import abstractmethod
from typing import List, Any, Dict, TypeVar, Type, final, Optional

from colorama import Fore
from graia.ariadne import Ariadne
from graia.ariadne.event.message import MessageEvent
from graia.ariadne.message.element import Forward, ForwardNode, Face
from graia.ariadne.model import Profile

from .analyze import is_crontab_expired


class Task:
    """
    A base class for tasks.

    Attributes:
        task_name (str): The name of the task.
        crontab (str): The crontab expression for scheduling the task.

    Methods:
        __init__(task_name: str, crontab: str):
            Initialize the Task with a task name and a crontab expression.
        make(app: Ariadne) -> Any:
            Abstract method to be implemented by subclasses. Perform the task.
        as_dict() -> Dict:
            Return a dictionary representation of the task.
        _as_dict() -> Dict:
            Abstract method to be implemented by subclasses. Return a dictionary representation of the task-specific data.
    """

    def __init__(self, task_name: str, crontab: str):
        self.task_name: str = task_name
        self.crontab: str = crontab

    @abstractmethod
    async def make(self, app: Ariadne) -> Any:
        pass

    @final
    def as_dict(self) -> Dict:
        temp: Dict = {"task_name": self.task_name, "crontab": self.crontab}
        temp.update(self._as_dict())
        return temp

    @abstractmethod
    def _as_dict(self) -> Dict:
        pass


class ReminderTask(Task):
    """
    A class representing a reminder task.

    Attributes:
        task_name (str): The name of the task.
        crontab (str): The crontab expression for scheduling the task.
        remind_content (List[int]): The list of message IDs to be sent as reminders.
        target (int): The target group ID to send the reminders to.

    Methods:
        __init__(task_name: str, crontab: str, remind_content: List[int], target: int):
            Initialize the ReminderTask with a task name, crontab expression, remind content, and target.
        make(app: Ariadne):
            Perform the reminder task.
        _as_dict() -> Dict:
            Return a dictionary representation of the ReminderTask.
    """

    def __init__(self, crontab: str, remind_content: List[int], target: int, task_name: Optional[str] = None):
        if task_name is None:
            time_stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
            task_name = f"{self.__class__.__name__}-{time_stamp}"
        super().__init__(task_name, crontab)
        self.remind_content: List[int] = remind_content
        self.target: int = target

    async def make(self, app: Ariadne):
        """
        Perform the reminder task.

        Args:
            app (Ariadne): The Ariadne application object.

        Returns:
            Callable: An async function that sends the reminder messages.
        """
        from graia.ariadne.message.chain import MessageChain

        nodes = []
        for msg_id in self.remind_content:
            msg_event: MessageEvent = await app.get_message_from_id(msg_id, self.target)

            nodes.append(
                ForwardNode(
                    msg_event.sender.id,
                    time=datetime.datetime.now(),
                    message=msg_event.message_chain,
                    name=msg_event.sender.name,
                )
            )
        profile: Profile = await app.get_bot_profile()
        nodes.append(
            ForwardNode(
                app.account,
                time=datetime.datetime.now(),
                message=MessageChain("不要忘了哦") + Face(name="玫瑰"),
                name=profile.nickname,
            )
        )

        async def _():
            await app.send_group_message(self.target, Forward(nodes))

        return _

    def _as_dict(self) -> Dict:
        """
        Return a dictionary representation of the ReminderTask.

        Returns:
            Dict: The dictionary representation of the ReminderTask.
        """
        return {"remind_content": self.remind_content, "target": self.target}


T_TASK = TypeVar("T_TASK", bound=Task)


class TaskRegistry(object):
    def __init__(
        self,
        save_path: str,
        task_type: Type[T_TASK],
    ):
        self._save_path: str = save_path
        self._task_type: Type[T_TASK] = task_type
        self._tasks: Dict[str, Dict[str, T_TASK]] = {}
        if pathlib.Path(save_path).exists():
            self.load_tasks()
            self.remove_outdated_tasks()

    @property
    def tasks(self) -> Dict[str, Dict[str, T_TASK]]:
        """
        Return the dictionary of tasks.

        :return: A dictionary containing tasks.
        :rtype: Dict[str, Dict[str, T_TASK]]
        """
        return self._tasks

    @property
    def task_list(self) -> List[T_TASK]:
        """
        Returns a list of all tasks in the task list.

        Parameters:
            None

        Returns:
            List[T_TASK]: A list of all tasks in the task list.
        """
        task_list: List[T_TASK] = []
        for tasks in self._tasks.values():
            for task in tasks.values():
                task: T_TASK
                task_list.append(task)
        return task_list

    def register_task(self, task: T_TASK):
        """
        Registers a task in the task manager.

        Args:
            task (T_TASK): The task to register.

        Raises:
            TypeError: If the task is not of the correct type.

        Returns:
            None
        """
        if not isinstance(task, self._task_type):
            raise TypeError(f"Task {task} is not of type {self._task_type}")
        if task.crontab in self._tasks:
            self._tasks[task.crontab][task.task_name] = task
        else:
            self._tasks[task.crontab] = {task.task_name: task}

    def remove_outdated_tasks(self):
        """
        Remove outdated tasks from the task dictionary.

        Parameters:
            None.

        Returns:
            None.
        """
        Unexpired_tasks: Dict[str, Dict[str, T_TASK]] = {}
        for crontab, tasks in self._tasks.items():
            if not is_crontab_expired(crontab):
                Unexpired_tasks[crontab] = tasks
        self._tasks = Unexpired_tasks

    def load_tasks(self):
        """
        Load tasks from a file.

        This function reads the tasks from a file specified by `self._save_path` and populates the `_tasks` dictionary
        based on the contents of the file. The file is expected to be in JSON format.

        Parameters:
            self (obj): The current instance of the class.

        Returns:
            None
        """
        with open(self._save_path, "r") as f:
            temp_dict: Dict[str, Dict[str, Dict[str, Any]]] = json.load(f)
        for crontab, tasks in temp_dict.items():
            self._tasks[crontab] = {}
            for task_name, task_data in tasks.items():
                self._tasks[crontab][task_name] = self._task_type(**task_data)

    def save_tasks(self):
        """
        Save the tasks to the specified file path.

        This function saves the tasks stored in the `_tasks` attribute to the file specified by `self._save_path`.
        The tasks are converted into a temporary dictionary structure, where each crontab is a key that maps to a dictionary of task names and their corresponding attributes.
        The temporary dictionary is then written to the file in JSON format.

        Parameters:
            None

        Returns:
            None
        """
        print(f"{Fore.MAGENTA}Saving tasks to {self._save_path}")
        temp_dict: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for crontab, tasks in self._tasks.items():
            temp_dict[crontab] = {}
            for task_name, task in tasks.items():
                task: T_TASK
                temp_dict[crontab][task_name] = task.as_dict()
        with open(self._save_path, "w") as f:
            json.dump(temp_dict, f, ensure_ascii=False, indent=2)

    def remove_all_task(self):
        """
        Remove all tasks from the task list.
        """
        self._tasks = {}
