import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routes import create_router
from .core.engine import Engine
from .db.repository import ApplicationRepository, ApplicationStore
from .schemas.rules_schemas import load_rules


@asynccontextmanager
async def _lifespan(app: FastAPI):
    if app.state.repository is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not set")
        app.state.repository = ApplicationRepository(database_url)
    yield


def create_app(repository: ApplicationStore | None = None) -> FastAPI:
    app = FastAPI(title="Credit scoring", lifespan=_lifespan)
    app.state.repository = repository
    app.include_router(create_router(Engine(load_rules())))
    return app


app = create_app()
