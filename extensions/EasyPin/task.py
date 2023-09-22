import json
import pathlib
from abc import abstractmethod
from typing import List, Any, Dict, TypeVar, Type, final

from graia.ariadne import Ariadne
from graia.ariadne.message.element import Forward

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
        self.task_name = task_name
        self.crontab = crontab

    @abstractmethod
    def make(self, app: Ariadne) -> Any:
        pass

    @final
    def as_dict(self) -> Dict:
        temp: Dict = {"task_name": self.task_name, "crontab": self.crontab}
        return temp.update(self._as_dict())

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

    def __init__(self, task_name: str, crontab: str, remind_content: List[int], target: int):
        super().__init__(task_name, crontab)
        self.remind_content = remind_content
        self.target = target

    def make(self, app: Ariadne):
        """
        Perform the reminder task.

        Args:
            app (Ariadne): The Ariadne application object.

        Returns:
            Callable: An async function that sends the reminder messages.
        """
        messages = [app.get_message_from_id(msg_id, self.target) for msg_id in self.remind_content]

        async def _():
            await app.send_group_message(self.target, Forward(messages))
            await app.send_group_message(self.target, "不要忘了哦")

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
        self._task_type: Type[T_TASK] = task_type
        self._tasks: Dict[str, Dict[str, T_TASK]] = {}
        if pathlib.Path(save_path).exists():
            self._save_path: str = save_path
            self.load_tasks()

    @property
    def tasks(self):
        return self._tasks

    def register_task(self, task: T_TASK):
        if not isinstance(task, self._task_type):
            raise TypeError(f"Task {task} is not of type {self._task_type}")
        if task.crontab in self._tasks:
            self._tasks[task.crontab][task.task_name] = task
        else:
            self._tasks[task.crontab] = {task.task_name: task}

    def remove_outdated_tasks(self):
        Unexpired_tasks: Dict[str, Dict[str, T_TASK]] = {}
        for crontab, tasks in self._tasks.items():
            if not is_crontab_expired(crontab):
                Unexpired_tasks[crontab] = tasks
        self._tasks = Unexpired_tasks

    def load_tasks(self):
        with open(self._save_path, "r") as f:
            temp_dict: Dict[str, Dict[str, Dict[str, Any]]] = json.load(f)
        for crontab, tasks in temp_dict.items():
            for task_name, task_data in tasks.items():
                self._tasks[crontab][task_name] = self._task_type(**task_data)

    def save_tasks(self):
        temp_dict: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for crontab, tasks in self._tasks.items():
            temp_dict[crontab] = {}
            for task_name, task in tasks.items():
                task: T_TASK
                temp_dict[crontab][task_name] = task.as_dict()
        with open(self._save_path, "w") as f:
            json.dump(temp_dict, f, ensure_ascii=False, indent=2)
