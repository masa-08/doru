from typing import List

from doru.types import Credential, Exchange, Task


class DaemonManager:
    def get_tasks(self) -> List[Task]:
        return []

    def add_task(self, task: Task):
        pass

    def remove_task(self, id) -> None:
        pass

    def start_task(self, id) -> None:
        pass

    def start_all_tasks(self) -> None:
        pass

    def stop_task(self, id) -> None:
        pass

    def stop_all_tasks(self) -> None:
        pass

    def add_cred(self, cred: Credential) -> None:
        pass

    def remove_cred(self, exchange: Exchange) -> None:
        pass


def create_daemon_manager() -> DaemonManager:
    return DaemonManager()
