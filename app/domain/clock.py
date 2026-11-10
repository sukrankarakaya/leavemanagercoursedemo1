"""Tek saat kaynağı: "bugün" ve "şimdi" yalnızca buradan okunur (docs/conventions.md)."""

from datetime import UTC, date, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Şu an, timezone-aware UTC."""
        ...

    def today(self) -> date:
        """Bugünün tarihi (UTC)."""
        ...


class SystemClock:
    """Gerçek sistem saati."""

    def now(self) -> datetime:
        return datetime.now(UTC)

    def today(self) -> date:
        return self.now().date()


class FixedClock:
    """Testler için sabit saat (docs/testing.md, Determinism)."""

    def __init__(self, moment: datetime) -> None:
        if moment.tzinfo is None or moment.utcoffset() != timedelta(0):
            raise ValueError("FixedClock requires a timezone-aware UTC datetime")
        self._moment = moment

    def now(self) -> datetime:
        return self._moment

    def today(self) -> date:
        return self._moment.date()
