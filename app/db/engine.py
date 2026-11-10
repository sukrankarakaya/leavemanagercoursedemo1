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
    # timeout: a writer waits up to 15 s for another writer instead of failing at once.
    kwargs: dict[str, Any] = {"connect_args": {"check_same_thread": False, "timeout": 15}}
    if _is_memory(parsed.database):
        # :memory: — every connection would see its own empty database without one shared pool.
        kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)
    event.listen(engine, "connect", _on_connect)
    event.listen(engine, "begin", _begin)
    return engine


IMMEDIATE = "sqlite_begin_immediate"


def writer(engine: Engine) -> Engine:
    """Same pool, but transactions take the write lock up front (unit of work, spec 0002)."""
    return engine.execution_options(**{IMMEDIATE: True})


def _on_connect(dbapi_connection: Any, _record: Any) -> None:
    # The driver must not open transactions on its own; "begin" below opens them explicitly.
    dbapi_connection.isolation_level = None
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def _begin(connection: Any) -> None:
    # Writer transactions take the write lock when they start: a read-then-write use case cannot
    # deadlock on the lock upgrade, so concurrent use cases serialize (spec 0002, AC-17).
    # Readers keep a plain (deferred) BEGIN and do not block each other.
    immediate = connection.get_execution_options().get(IMMEDIATE, False)
    connection.exec_driver_sql("BEGIN IMMEDIATE" if immediate else "BEGIN")


def ensure_sqlite_directory(url: str) -> None:
    """Dosya tabanlı SQLite için üst klasörü oluşturur (ör. data/)."""
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite" and not _is_memory(parsed.database):
        Path(str(parsed.database)).parent.mkdir(parents=True, exist_ok=True)
