"""Alembic ortamı: bağlantı app.db.engine ile açılır, PRAGMA'lar migration'da da geçerli."""

import os

from alembic import context

from app.db.engine import make_engine
from app.db.models import Base

DEFAULT_URL = "sqlite:///data/app.db"


def _url() -> str:
    configured = context.config.get_main_option("sqlalchemy.url")
    return configured or os.environ.get("DATABASE_URL", DEFAULT_URL)


def run_offline() -> None:
    context.configure(url=_url(), target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_online() -> None:
    engine = make_engine(_url())
    try:
        with engine.connect() as connection:
            # render_as_batch: SQLite ALTER TABLE sınırlamaları için.
            context.configure(
                connection=connection, target_metadata=Base.metadata, render_as_batch=True
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()  # Windows: dosya kilidi kalmasın.


if context.is_offline_mode():
    run_offline()
else:
    run_online()
