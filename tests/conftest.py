"""Ortak test fixture'ları: sabit saat, test başına geçici veritabanı (docs/testing.md)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domain.clock import FixedClock

FIXED_NOW = datetime(2026, 11, 8, 9, 30, tzinfo=UTC)


@pytest.fixture
def fixed_clock() -> FixedClock:
    return FixedClock(FIXED_NOW)


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    """Bu teste özel, test bitince silinen SQLite dosyası."""
    return f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
