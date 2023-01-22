from dependency_injector import containers, providers

from doru.envs import DORU_CREDENTIAL_FILE, DORU_TASK_FILE, DORU_TASK_LIMIT
from doru.manager.credential_manager import CredentialManager
from doru.manager.task_manager import TaskManager


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["doru.api.router"])
    credential_manager: providers.Factory[CredentialManager] = providers.Factory(
        CredentialManager, file=DORU_CREDENTIAL_FILE
    )
    task_manager: providers.Singleton[TaskManager] = providers.Singleton(
        TaskManager, file=DORU_TASK_FILE, max_running_tasks=DORU_TASK_LIMIT
    )
