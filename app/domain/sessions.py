"""Oturum süre kuralı (spec 0002, R-8): 30 dk hareketsizlik, girişten 8 saat mutlak sınır."""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta

IDLE_TIMEOUT = timedelta(minutes=30)
ABSOLUTE_TIMEOUT = timedelta(hours=8)


@dataclass(frozen=True)
class SessionRecord:
    token_hash: str
    user_id: str
    created_at: datetime
    last_seen_at: datetime


def hash_token(token: str) -> str:
    """Veritabanında yalnızca bu özet durur; ham kimlik yalnızca cookie'de."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def is_expired(record: SessionRecord, now: datetime) -> bool:
    """Tam 30 dk hareketsizlikte veya tam 8 saatte oturum geçersizdir."""
    return now - record.last_seen_at >= IDLE_TIMEOUT or now - record.created_at >= ABSOLUTE_TIMEOUT
