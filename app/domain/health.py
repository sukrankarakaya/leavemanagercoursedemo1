"""Sistem sağlık raporu."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HealthReport:
    """Sistem ve veritabanı ayakta; rapor anındaki sunucu zamanı (UTC)."""

    server_time: datetime
    database_ok: bool = True
