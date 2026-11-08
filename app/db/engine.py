"""Engine kurulumu; SQLite tuzakları (conventions.md, Known traps 1–2) tek yerde çözülür."""

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.pool import StaticPool


def _is_memory(database: str | None) -> bool:
    return database in (None, "", ":memory:")


def make_engine(url: str) -> Engine:
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite":
        return create_engine(url)
    kwargs: dict[str, Any] = {"connect_args": {"check_same_thread": False}}
    if _is_memory(parsed.database):
        # :memory: — every connection would see its own empty database without one shared pool.
        kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def _enable_foreign_keys(dbapi_connection: Any, _record: Any) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def ensure_sqlite_directory(url: str) -> None:
    """Dosya tabanlı SQLite için üst klasörü oluşturur (ör. data/)."""
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite" and not _is_memory(parsed.database):
        Path(str(parsed.database)).parent.mkdir(parents=True, exist_ok=True)
