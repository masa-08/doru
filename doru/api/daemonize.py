import asyncio
import logging
import os
import signal
from multiprocessing import Process
from pathlib import Path

import backoff
import uvicorn
from daemon.daemon import DaemonContext
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pid import PidFile
from requests.exceptions import RequestException

from doru.api.client import Client, create_client
from doru.api.schema import KeepAlive
from doru.envs import DORU_PID_FILE, DORU_SOCK_NAME

TIMEOUT = 10

logger = logging.getLogger("doru")
router_daemonize = APIRouter()


@backoff.on_exception(backoff.expo, RequestException, max_time=TIMEOUT, raise_on_giveup=False)
async def wait_until_alive(client: Client, is_alive: asyncio.Event) -> None:
    client.keepalive()
    is_alive.set()


async def run() -> None:
    process = Process(target=_run)
    process.start()

    # Wait until the daemon is up and running.
    client = create_client()
    is_alive = asyncio.Event()
    asyncio.create_task(wait_until_alive(client, is_alive))
    await asyncio.wait_for(is_alive.wait(), TIMEOUT)


def _run(pidfile: str = DORU_PID_FILE, sockfile: str = DORU_SOCK_NAME) -> None:
    pid_path = Path(pidfile).expanduser()
    pid_path_parent = pid_path.parent
    sock_path = Path(sockfile).expanduser()
    sock_path_parent = sock_path.parent

    try:
        if not os.path.exists(pid_path_parent):
            pid_path_parent.mkdir(parents=True)
        if not os.path.exists(sock_path_parent):
            sock_path_parent.mkdir(parents=True)
    except OSError:
        logger.fatal("Could not create directories to manage doru application.")
        exit(1)

    # TODO: improve logging
    with DaemonContext(pidfile=PidFile(str(pid_path)), detach_process=True):
        uvicorn.run("doru.api.app:app", host="0.0.0.0", uds=str(sock_path))


@router_daemonize.post("/terminate", status_code=status.HTTP_204_NO_CONTENT)
def terminate():
    try:
        os.kill(os.getpid(), signal.SIGTERM)
    except OSError as e:
        logger.error(str(e))
        return JSONResponse(
            content={
                "detail": "\
Could not delete application daemon process. \
If necessary, the PID of the daemon process can be obtained from the `/keepalive` endpoint \
and removed with the `kill` command."
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router_daemonize.get("/keepalive", response_model=KeepAlive, status_code=status.HTTP_200_OK)
def keepalive():
    return KeepAlive(pid=os.getpid())
