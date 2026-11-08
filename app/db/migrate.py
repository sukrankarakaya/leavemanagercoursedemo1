"""Şemayı kayıtlı migration geçmişinden kurar (spec 0001, R-3)."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.db.engine import ensure_sqlite_directory

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def alembic_config(url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def upgrade_to_head(url: str) -> None:
    """Veritabanını en güncel şema sürümüne getirir; zaten güncelse hiçbir şey yapmaz."""
    ensure_sqlite_directory(url)
    command.upgrade(alembic_config(url), "head")
