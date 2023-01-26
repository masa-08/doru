from fastapi import FastAPI

from doru.api.daemonize import router_daemonize
from doru.api.router import router
from doru.manager.container import Container


def create_app() -> FastAPI:
    container = Container()
    app = FastAPI()
    setattr(app, "container", container)
    app.include_router(router)
    app.include_router(router_daemonize)
    return app


app = create_app()
