"""Uygulama kurulumu (composition root).

Çalıştırma: tools/venv uvicorn app.main:create_app --factory
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.errors import install_error_handlers
from app.api.health import router as health_router
from app.api.users import router as users_router
from app.config import Settings
from app.db.engine import make_engine
from app.db.migrate import upgrade_to_head
from app.domain.clock import Clock, SystemClock
from app.repositories.health_repository import SqlHealthRepository
from app.repositories.unit_of_work import SqlUnitOfWorkFactory
from app.services.auth_service import AuthService
from app.services.health_service import HealthService
from app.services.passwords import Argon2PasswordHasher, PasswordHasher
from app.services.user_service import UserService

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def create_app(
    settings: Settings | None = None,
    clock: Clock | None = None,
    *,
    migrate: bool = True,
    hasher: PasswordHasher | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    clock = clock or SystemClock()
    hasher = hasher or Argon2PasswordHasher()
    engine = make_engine(settings.database_url)
    uow = SqlUnitOfWorkFactory(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        if migrate:
            upgrade_to_head(settings.database_url)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="İzin Yöneticisi", lifespan=lifespan)
    app.state.settings = settings
    app.state.health_service = HealthService(SqlHealthRepository(engine), clock)
    app.state.auth_service = AuthService(uow, hasher, clock)
    app.state.user_service = UserService(uow, hasher, clock)
    install_error_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
