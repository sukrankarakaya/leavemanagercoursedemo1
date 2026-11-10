"""Tek kullanım senaryosu = tek DB transaction'ı (docs/architecture.md; plan 0002 A-1).

Başarıda commit, istisnada rollback. Yazma kilidi transaction başında alınır (app.db.engine.writer).
"""

from types import TracebackType
from typing import Self

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.engine import writer
from app.repositories.session_repository import SqlSessionRepository
from app.repositories.throttle_repository import SqlThrottleRepository
from app.repositories.user_repository import SqlUserRepository


class SqlUnitOfWork:
    users: SqlUserRepository
    sessions: SqlSessionRepository
    throttle: SqlThrottleRepository

    def __init__(self, factory: "sessionmaker[Session]") -> None:
        self._factory = factory
        self._session: Session | None = None

    def __enter__(self) -> Self:
        session = self._factory()
        session.begin()
        self._session = session
        self.users = SqlUserRepository(session)
        self.sessions = SqlSessionRepository(session)
        self.throttle = SqlThrottleRepository(session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        session = self._session
        assert session is not None  # noqa: S101 — __enter__ always runs first
        try:
            if exc_type is None:
                session.commit()
            else:
                session.rollback()
        finally:
            session.close()
            self._session = None


class SqlUnitOfWorkFactory:
    """Her çağrıda yeni bir unit of work (servisler kullanım senaryosu başına bir tane açar)."""

    def __init__(self, engine: Engine) -> None:
        self._factory = sessionmaker(writer(engine), expire_on_commit=False)

    def __call__(self) -> SqlUnitOfWork:
        return SqlUnitOfWork(self._factory)
