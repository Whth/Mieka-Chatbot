from graia.scheduler import SchedulerTask


class ScheduledTask(object):
    def __init__(self, task: SchedulerTask, task_name: str):
        self._task: SchedulerTask = task
        self._task_name: str = task_name

    @property
    def task(self):
        return self._task

    @property
    def task_name(self):
        return self._task_name
