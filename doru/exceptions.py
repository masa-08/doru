class DoruError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class TaskNotExist(DoruError):
    def __init__(self, id: str) -> None:
        message = f"The task ID {id} does not exist."
        super().__init__(message)


class TaskDuplicate(DoruError):
    def __init__(self, id: str) -> None:
        message = f"The task ID {id} is duplicated."
        super().__init__(message)


class MoreThanMaxRunningTasks(DoruError):
    def __init__(self, max_running_tasks: int) -> None:
        message = f"The maximum number of tasks({max_running_tasks}) that can be executed has been exceeded."
        super().__init__(message)
