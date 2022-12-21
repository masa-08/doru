from typing import List

from doru.api.schema import Credential, Task, TaskCreate
from doru.envs import DORU_SOCK_NAME
from doru.session import create_client
from doru.types import Exchange, Interval, Pair


class DaemonManager:
    def __init__(self, sock: str) -> None:
        self.client = create_client(sock)

    def get_tasks(self) -> List[Task]:
        res = self.client.get("tasks")
        res.raise_for_status()
        data = res.json()
        return [
            Task(
                id=d["id"],
                pair=d["pair"],
                amount=d["amount"],
                interval=d["interval"],
                exchange=d["exchange"],
                status=d["status"],
            )
            for d in data
        ]

    def add_task(self, exchange: Exchange, interval: Interval, amount: int, pair: Pair) -> Task:
        task = TaskCreate(pair=pair, amount=amount, interval=interval, exchange=exchange)
        res = self.client.post("tasks", data=task.json())
        res.raise_for_status()
        data = res.json()
        return Task(
            id=data["id"],
            pair=data["pair"],
            amount=data["amount"],
            interval=data["interval"],
            exchange=data["exchange"],
            status=data["status"],
        )

    def remove_task(self, id: str) -> None:
        res = self.client.delete(f"tasks/{id}")
        res.raise_for_status()

    def start_task(self, id: str) -> None:
        res = self.client.post(f"tasks/{id}/start")
        res.raise_for_status()

    def start_all_tasks(self) -> None:
        tasks = self.get_tasks()
        for task in tasks:
            self.start_task(task.id)

    def stop_task(self, id: str) -> None:
        res = self.client.post(f"tasks/{id}/stop")
        res.raise_for_status()

    def stop_all_tasks(self) -> None:
        tasks = self.get_tasks()
        for task in tasks:
            self.stop_task(task.id)

    def add_cred(self, exchange: Exchange, key: str, secret: str) -> None:
        cred = Credential(exchange=exchange, key=key, secret=secret)
        res = self.client.post("cred", data=cred.json())
        res.raise_for_status()

    def remove_cred(self, exchange: Exchange) -> None:
        res = self.client.delete(f"cred/{exchange}")
        res.raise_for_status()


def create_daemon_manager(sock: str = DORU_SOCK_NAME) -> DaemonManager:
    return DaemonManager(sock)
