"""AC-3: şema kurulumu, tekrar çalıştırmada değişiklik yok, her bağlantıda foreign key zorlaması."""

from alembic.script import ScriptDirectory
from sqlalchemy import Engine, text

from app.db.engine import make_engine
from app.db.migrate import alembic_config, upgrade_to_head


def _versions(engine: Engine) -> list[str]:
    with engine.connect() as connection:
        return list(connection.execute(text("SELECT version_num FROM alembic_version")).scalars())


def test_upgrade_installs_head_and_is_idempotent(db_url: str) -> None:
    head = ScriptDirectory.from_config(alembic_config(db_url)).get_current_head()
    assert head is not None

    upgrade_to_head(db_url)
    engine = make_engine(db_url)
    try:
        assert _versions(engine) == [head]
        upgrade_to_head(db_url)
        assert _versions(engine) == [head]
    finally:
        engine.dispose()


def test_every_connection_enforces_foreign_keys(db_url: str) -> None:
    upgrade_to_head(db_url)
    engine = make_engine(db_url)
    try:
        with engine.connect() as first, engine.connect() as second:
            assert first.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
            assert second.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        engine.dispose()  # havuz boşalır; sonraki bağlantı yepyeni açılır
        with engine.connect() as fresh:
            assert fresh.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
    finally:
        engine.dispose()


def test_memory_database_is_shared_across_connections() -> None:
    engine = make_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE probe (id INTEGER PRIMARY KEY)"))
        with engine.connect() as other:
            assert other.execute(text("SELECT count(*) FROM probe")).scalar() == 0
    finally:
        engine.dispose()
