"""Sistem sağlık kontrolü (spec 0001, R-1/R-2)."""

from typing import Protocol

from app.domain.clock import Clock
from app.domain.health import HealthReport


class DatabaseProbe(Protocol):
    def ping(self) -> None:
        """Veritabanına ulaşır; ulaşamazsa DatabaseUnavailableError fırlatır."""
        ...


class HealthService:
    def __init__(self, probe: DatabaseProbe, clock: Clock) -> None:
        self._probe = probe
        self._clock = clock

    def check(self) -> HealthReport:
        """Veritabanı erişilebilirse raporu döner; değilse DatabaseUnavailableError yükselir."""
        self._probe.ping()
        return HealthReport(server_time=self._clock.now())
