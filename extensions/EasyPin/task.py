import pathlib
import pickle
from typing import List, Coroutine, Any, Callable

Task = Callable[[], Coroutine[Any, Any, Any]]

from .analyze import is_crontab_expired


class ScheduledTask(object):
    def __init__(self, task: Task, task_name: str, task_crontab: str):
        self._task: Task = task
        self._task_name: str = task_name
        self._task_crontab: str = task_crontab

    @property
    def task(self) -> Task:
        return self._task

    @property
    def task_name(self) -> str:
        return self._task_name

    @property
    def task_crontab(self) -> str:
        return self._task_crontab


class TaskRegistry(object):
    def __init__(self, save_path: str):
        self._tasks: List[ScheduledTask] = []
        self._save_path: str = save_path
        if pathlib.Path(save_path).exists():
            self.load_tasks()

    def register_task(self, task: Task, task_name: str, task_crontab: str):
        self._tasks.append(ScheduledTask(task, task_name, task_crontab))

    def remove_outdated_tasks(self):
        Unexpired_tasks = []
        for task in self._tasks:
            if not is_crontab_expired(task.task_crontab):
                Unexpired_tasks.append(task)
        self._tasks = Unexpired_tasks

    def load_tasks(self):
        with open(self._save_path, "rb") as f:
            self._tasks = pickle.load(f)
        self.remove_outdated_tasks()

    def save_tasks(self):
        pathlib.Path(self._save_path).mkdir(parents=True, exist_ok=True)
        with open(self._save_path, "wb") as f:
            pickle.dump(self._tasks, f)
