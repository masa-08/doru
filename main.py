import uvicorn

from doru.api.app import create_app
from doru.logger import init_logger

app = create_app()

if __name__ == "__main__":
    init_logger()
    uvicorn.run("main:app", host="0.0.0.0")  # remove after daemonize
