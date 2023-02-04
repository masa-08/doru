from typing import List

from doru.api.schema import Credential, KeepAlive, Task, TaskCreate
from doru.api.session import create_session
from doru.envs import DORU_SOCK_NAME
from doru.types import Cycle, Exchange, Pair


class Client:
    def __init__(self, sock: str) -> None:
        self.session = create_session(sock)

    def get_tasks(self) -> List[Task]:
        res = self.session.get("tasks")
        res.raise_for_status()
        data = res.json()
        return [
            Task(
                id=d["id"],
                pair=d["pair"],
                amount=d["amount"],
                cycle=d["cycle"],
                exchange=d["exchange"],
                status=d["status"],
            )
            for d in data
        ]

    def add_task(self, exchange: Exchange, cycle: Cycle, amount: int, pair: Pair) -> Task:
        task = TaskCreate(pair=pair, amount=amount, cycle=cycle, exchange=exchange)
        res = self.session.post("tasks", data=task.json())
        res.raise_for_status()
        data = res.json()
        return Task(
            id=data["id"],
            pair=data["pair"],
            amount=data["amount"],
            cycle=data["cycle"],
            exchange=data["exchange"],
            status=data["status"],
        )

    def remove_task(self, id: str) -> None:
        res = self.session.delete(f"tasks/{id}")
        res.raise_for_status()

    def start_task(self, id: str) -> None:
        res = self.session.post(f"tasks/{id}/start")
        res.raise_for_status()

    def start_all_tasks(self) -> None:
        tasks = self.get_tasks()
        for task in tasks:
            self.start_task(task.id)

    def stop_task(self, id: str) -> None:
        res = self.session.post(f"tasks/{id}/stop")
        res.raise_for_status()

    def stop_all_tasks(self) -> None:
        tasks = self.get_tasks()
        for task in tasks:
            self.stop_task(task.id)

    def add_cred(self, exchange: Exchange, key: str, secret: str) -> None:
        cred = Credential(exchange=exchange, key=key, secret=secret)
        res = self.session.post("credentials", data=cred.json())
        res.raise_for_status()

    def remove_cred(self, exchange: Exchange) -> None:
        res = self.session.delete(f"credentials/{exchange}")
        res.raise_for_status()

    def keepalive(self) -> KeepAlive:
        res = self.session.get("keepalive")
        res.raise_for_status()
        data = res.json()
        return KeepAlive(pid=data["pid"])

    def terminate(self) -> None:
        res = self.session.post("terminate")
        res.raise_for_status()


def create_client(sock: str = DORU_SOCK_NAME) -> Client:
    return Client(sock)
