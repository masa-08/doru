from logging import getLogger
from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from doru.api.schema import Credential, Task, TaskCreate
from doru.exceptions import MoreThanMaxRunningTasks, TaskDuplicate, TaskNotExist
from doru.manager.container import Container
from doru.manager.credential_manager import CredentialManager
from doru.manager.task_manager import TaskManager
from doru.types import Exchange

router = APIRouter()
logger = getLogger("doru")


INTERNAL_ERROR_MESSAGE = "An internal error has occurred."


@router.get("/tasks", response_model=List[Task], status_code=status.HTTP_200_OK)
@inject
def get_tasks(manager: TaskManager = Depends(Provide[Container.task_manager])):
    return manager.get_tasks()


@router.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
@inject
def post_task(task: TaskCreate, manager: TaskManager = Depends(Provide[Container.task_manager])):
    try:
        t: Task = manager.add_task(task)
    except Exception as e:
        logger.error(str(e))
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return t


@router.post("/tasks/{task_id}/start", status_code=status.HTTP_204_NO_CONTENT)
@inject
def post_start_task(task_id: str, manager: TaskManager = Depends(Provide[Container.task_manager])):
    try:
        manager.start_task(task_id)
    except TaskNotExist as e:
        logger.error(str(e))
        return JSONResponse(content={"detail": str(e)}, status_code=status.HTTP_404_NOT_FOUND)
    except TaskDuplicate as e:
        logger.error(str(e))
        return JSONResponse(
            content={"detail": f"The task with ID {task_id} has already started."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except MoreThanMaxRunningTasks as e:
        logger.error(str(e))
        return JSONResponse(content={"detail": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(str(e))
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/tasks/{task_id}/stop", status_code=status.HTTP_204_NO_CONTENT)
@inject
def post_stop_task(task_id: str, manager: TaskManager = Depends(Provide[Container.task_manager])):
    try:
        manager.stop_task(task_id)
    except TaskNotExist as e:
        logger.error(str(e))
        return JSONResponse(content={"detail": str(e)}, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(str(e))
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
def delete_task(task_id: str, manager: TaskManager = Depends(Provide[Container.task_manager])):
    try:
        manager.remove_task(task_id)
    except KeyError as e:
        logger.error(str(e))
        return JSONResponse(
            content={"detail": f"The task ID {task_id} does not exist."}, status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(str(e))
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/credentials", status_code=status.HTTP_201_CREATED)
@inject
def post_credential(cred: Credential, manager: CredentialManager = Depends(Provide[Container.credential_manager])):
    try:
        manager.add_credential(cred)
    except Exception as e:
        logger.error(str(e))
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/credentials/{exchange}")
@inject
def delete_credential(exchange: Exchange, manager: CredentialManager = Depends(Provide[Container.credential_manager])):
    try:
        manager.remove_credential(exchange)
    except KeyError as e:
        logger.error(str(e))
        return JSONResponse(
            content={"detail": f"The credential of {exchange} does not exist."}, status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(str(e))
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
