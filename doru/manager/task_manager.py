import json
import os
from copy import deepcopy
from logging import getLogger
from pathlib import Path
from shutil import copyfile
from typing import Any, Callable, Dict, List

from nanoid import generate

from doru.api.schema import Task, TaskCreate
from doru.envs import DORU_TASK_FILE, DORU_TASK_LIMIT
from doru.exceptions import (
    DoruError,
    MoreThanMaxRunningTasks,
    TaskDuplicate,
    TaskNotExist,
)
from doru.scheduler import ScheduleThreadPool

logger = getLogger("doru")


def dummy_func() -> None:
    pass


class TaskManager:
    tasks: Dict[str, Task]
    _id_len = 12

    def __init__(self, file: str, max_running_tasks: int) -> None:
        self.file = Path(file).expanduser()
        self.pool = ScheduleThreadPool(max_running_threads=max_running_tasks)
        self._max_running_tasks = max_running_tasks
        try:
            self._read()
            # Start tasks with running status
            for t in self.tasks.values():
                if t.status == "Running":
                    self.start_task(t.id)
        except FileNotFoundError:
            logger.warning("Task file for this application could not be found.")
            self.tasks = {}

            if not os.path.exists(self.file.parent):
                self.file.parent.mkdir(parents=True)
            self._write()
        except Exception as e:
            logger.error(f"Failed to read the Task file: {e}")
            raise e

    def _rollback(func: Callable[..., Any]):  # type:ignore[misc]
        """
        A decorator that performs rollback processing when an error occurs in any of the operations associated
        with a task. It does not perform rollback processing for the thread pool, so it must be implemented separately
        when some processing is required for the thread pool.
        """

        def wrapper(self, *args, **kwargs):
            tasks_backup = deepcopy(self.tasks)
            tasks_file_backup = f"{self.file}_bk_{generate()}"
            copyfile(src=self.file, dst=tasks_file_backup)

            try:
                result = func(self, *args, **kwargs)
            except Exception:
                self.tasks = tasks_backup
                copyfile(src=tasks_file_backup, dst=self.file)
                raise
            finally:
                os.remove(tasks_file_backup)
            return result

        return wrapper

    def _read(self) -> None:
        with open(self.file, "r") as f:
            tasks = json.load(f)
            # raise ValidationError when v is incompatible with Task class
            self.tasks = {k: Task.parse_obj(v) for (k, v) in tasks.items()}

    def _write(self) -> None:
        with open(self.file, "w") as f:
            task_dict = {k: v.dict() for (k, v) in self.tasks.items()}
            json.dump(task_dict, f)

    def get_tasks(self) -> List[Task]:
        return list(self.tasks.values())

    @_rollback
    def add_task(self, task: TaskCreate) -> Task:
        id = generate(size=self._id_len)
        new_task = Task(
            id=id, pair=task.pair, amount=task.amount, interval=task.interval, exchange=task.exchange, status="Stopped"
        )
        self.tasks[id] = new_task
        self._write()
        return new_task

    @_rollback
    def remove_task(self, id: str) -> None:
        self.tasks.pop(id)
        self._write()
        self.pool.kill(id)

    @_rollback
    def start_task(self, id: str) -> None:
        task = self.tasks.get(id)
        if task is None:
            raise TaskNotExist(id)

        self.tasks[id].status = "Running"
        self._write()

        try:
            # TODO: replace dummy_func after inplementing of crypto trading function.
            self.pool.submit(key=id, func=dummy_func, interval=task.interval)
        except DoruError:
            raise TaskDuplicate(id)

        try:
            self.pool.start(id)
        except DoruError:
            self.pool.kill(id)
            raise MoreThanMaxRunningTasks(self._max_running_tasks)
        except Exception:
            self.pool.kill(id)
            raise

    @_rollback
    def stop_task(self, id: str) -> None:
        if self.tasks.get(id) is None:
            raise TaskNotExist(id)

        self.tasks[id].status = "Stopped"
        self._write()
        self.pool.kill(id)


def create_task_manager(file: str = DORU_TASK_FILE, max_running_tasks: int = DORU_TASK_LIMIT) -> TaskManager:
    return TaskManager(file, max_running_tasks)
