"""Veritabanı erişilebilirlik sorgusu (services.health_service.DatabaseProbe uygulaması)."""

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.domain.errors import DatabaseUnavailableError


class SqlHealthRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ping(self) -> None:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError() from exc
