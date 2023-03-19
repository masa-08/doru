import json
import os
from logging import getLogger
from pathlib import Path
from typing import Dict, List, Optional

from nanoid import generate
from retry import retry

from doru.api.schema import TIMESTAMP_STRING_FORMAT, Task, TaskCreate
from doru.envs import DORU_TASK_FILE, DORU_TASK_LIMIT
from doru.exceptions import (
    DoruError,
    MoreThanMaxRunningTasks,
    OrderNotComplete,
    OrderNotCreated,
    OrderStatusUnknown,
    TaskDuplicate,
    TaskNotExist,
)
from doru.exchange import OrderStatus, get_exchange
from doru.manager.utils import rollback
from doru.scheduler import ScheduleThreadPool

logger = getLogger(__name__)


@retry(tries=5, exceptions=(OrderNotCreated, OrderNotComplete))
def do_order(*args, **kwargs) -> None:
    if not kwargs.keys() >= {"exchange_name", "symbol", "amount"}:
        raise ValueError("Requied args are missing. required args: `exchange_name, symbol, amount`")
    exchange = get_exchange(kwargs["exchange_name"])

    try:
        order_id = exchange.create_order(kwargs["symbol"], kwargs["amount"])
    except Exception as e:
        raise OrderNotCreated(str(e))

    order_status = exchange.wait_order_complete(order_id, kwargs["symbol"])
    if order_status is None:
        raise OrderStatusUnknown(order_id)
    elif order_status in (OrderStatus.CANCELED.value, OrderStatus.EXPIRED.value, OrderStatus.REJECTED.value):
        raise OrderNotComplete(order_id)
    elif order_status == OrderStatus.OPEN.value:
        try:
            exchange.cancel_order(order_id, kwargs["symbol"])
        except Exception:
            raise DoruError(f"Failed to cancel order: {{'order_id': {order_id}}}")
        else:
            raise OrderNotComplete(order_id)


class TaskManager:
    tasks: Dict[str, Task]
    _size = 12
    _alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

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

    def _read(self) -> None:
        with open(self.file, "r") as f:
            tasks = json.load(f)
            # raise ValidationError when v is incompatible with Task class
            self.tasks = {k: Task.parse_obj(v) for (k, v) in tasks.items()}

    def _write(self) -> None:
        with open(self.file, "w") as f:
            task_dict = {k: v.dict(exclude_none=True) for (k, v) in self.tasks.items()}
            json.dump(task_dict, f)

    def get_tasks(self) -> List[Task]:
        # update next_run fields
        for k, v in self.tasks.items():
            self.tasks[k].next_run = self._get_next_run(k)
        return list(self.tasks.values())

    @rollback(properties=["tasks"], files=["file"])
    def add_task(self, task: TaskCreate) -> Task:
        id = generate(size=self._size, alphabet=self._alphabet)
        new_task = Task(
            symbol=task.symbol,
            amount=task.amount,
            cycle=task.cycle,
            weekday=task.weekday,
            day=task.day,
            time=task.time,
            exchange=task.exchange,
            id=id,
            status="Stopped",
        )
        self.tasks[id] = new_task
        self._write()
        return new_task

    @rollback(properties=["tasks"], files=["file"])
    def remove_task(self, id: str) -> None:
        self.tasks.pop(id)
        self._write()
        self.pool.kill(id)

    @rollback(properties=["tasks"], files=["file"])
    def start_task(self, id: str) -> None:
        task = self.tasks.get(id)
        if task is None:
            raise TaskNotExist(id)

        self.tasks[id].status = "Running"
        self._write()

        try:
            self.pool.submit(
                key=id,
                func=do_order,
                cycle=task.cycle,
                weekday=task.weekday,
                day=task.day,
                time=task.time,
                exchange_name=task.exchange,
                symbol=task.symbol,
                amount=task.amount,
            )
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

    @rollback(properties=["tasks"], files=["file"])
    def stop_task(self, id: str) -> None:
        if self.tasks.get(id) is None:
            raise TaskNotExist(id)

        self.tasks[id].status = "Stopped"
        self._write()
        self.pool.kill(id)

    def _get_next_run(self, id: str) -> Optional[str]:
        next_run = self.pool.next_run(id)
        if next_run is not None:
            return next_run.strftime(TIMESTAMP_STRING_FORMAT)
        return None


def create_task_manager(file: str = DORU_TASK_FILE, max_running_tasks: int = DORU_TASK_LIMIT) -> TaskManager:
    return TaskManager(file, max_running_tasks)
