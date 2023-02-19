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

router = APIRouter()
logger = getLogger(__name__)


INTERNAL_ERROR_MESSAGE = "An internal error has occurred."


@router.get("/tasks", response_model=List[Task], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
@inject
def get_tasks(manager: TaskManager = Depends(Provide[Container.task_manager])):
    return manager.get_tasks()


@router.post("/tasks", response_model=Task, response_model_exclude_none=True, status_code=status.HTTP_201_CREATED)
@inject
def post_task(task: TaskCreate, manager: TaskManager = Depends(Provide[Container.task_manager])):
    logger.info(f"Adding task: {task.dict()}")
    try:
        t: Task = manager.add_task(task)
    except Exception as e:
        logger.error(f"Failed to add task: {str(e)}")
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    logger.info(f"Added task: {t.dict()}")
    return t


@router.post("/tasks/{task_id}/start", status_code=status.HTTP_204_NO_CONTENT)
@inject
def post_start_task(task_id: str, manager: TaskManager = Depends(Provide[Container.task_manager])):
    logger.info(f"Starting task: {{'id': {task_id}}}")
    try:
        manager.start_task(task_id)
    except TaskNotExist as e:
        logger.error(f"Failed to start task: {str(e)}")
        return JSONResponse(content={"detail": str(e)}, status_code=status.HTTP_404_NOT_FOUND)
    except TaskDuplicate as e:
        logger.error(f"Failed to start task: {str(e)}")
        return JSONResponse(
            content={"detail": f"The task with ID {task_id} has already started."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except MoreThanMaxRunningTasks as e:
        logger.error(f"Failed to start task: {str(e)}")
        return JSONResponse(content={"detail": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Failed to start task: {str(e)}")
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    logger.info(f"Started task: {{'id': {task_id}}}")


@router.post("/tasks/{task_id}/stop", status_code=status.HTTP_204_NO_CONTENT)
@inject
def post_stop_task(task_id: str, manager: TaskManager = Depends(Provide[Container.task_manager])):
    logger.info(f"Stopping task: {{'id': {task_id}}}")
    try:
        manager.stop_task(task_id)
    except TaskNotExist as e:
        logger.error(f"Failed to stop task: {str(e)}")
        return JSONResponse(content={"detail": str(e)}, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Failed to stop task: {str(e)}")
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    logger.info(f"Stopped task: {{'id': {task_id}}}")


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
def delete_task(task_id: str, manager: TaskManager = Depends(Provide[Container.task_manager])):
    logger.info(f"Removing task: {{'id': {task_id}}}")
    try:
        manager.remove_task(task_id)
    except KeyError as e:
        logger.error(f"Failed to remove task: {str(e)}")
        return JSONResponse(
            content={"detail": f"The task ID {task_id} does not exist."}, status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Failed to remove task: {str(e)}")
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    logger.info(f"Removed task: {{'id': {task_id}}}")


@router.post("/credentials", status_code=status.HTTP_201_CREATED)
@inject
def post_credential(cred: Credential, manager: CredentialManager = Depends(Provide[Container.credential_manager])):
    logger.info(f"Adding credential: {{'exchange': {cred.exchange}}}")
    try:
        manager.add_credential(cred)
    except Exception as e:
        logger.error(f"Failed to add credential: {str(e)}")
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    logger.info(f"Added credential: {{'exchange': {cred.exchange}}}")


@router.delete("/credentials/{exchange}")
@inject
def delete_credential(exchange: str, manager: CredentialManager = Depends(Provide[Container.credential_manager])):
    logger.info(f"Removing credential: {{'exchange': {exchange}}}")
    try:
        manager.remove_credential(exchange)
    except KeyError as e:
        logger.error(f"Failed to remove credential: {str(e)}")
        return JSONResponse(
            content={"detail": f"The credential of {exchange} does not exist."}, status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Failed to remove credential: {str(e)}")
        return JSONResponse(
            content={"detail": INTERNAL_ERROR_MESSAGE}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    logger.info(f"Removed credential: {{'exchange': {exchange}}}")
