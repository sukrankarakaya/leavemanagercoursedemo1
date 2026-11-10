"""Ayarlar ortam değişkenlerinden okunur; .env dosyası okunmaz (.env.example belgeler)."""

import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "sqlite:///data/app.db"


@dataclass(frozen=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
