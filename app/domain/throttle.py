"""Giriş denemesi sınırı (spec 0002, R-10): 15 dk içinde 5 başarısız → 15 dk kilit."""

from datetime import datetime, timedelta

MAX_FAILURES = 5
FAILURE_WINDOW = timedelta(minutes=15)
LOCK_DURATION = timedelta(minutes=15)


def window_start(now: datetime) -> datetime:
    """Bu andan sonraki başarısızlıklar sayılır; daha eskileri sayılmaz."""
    return now - FAILURE_WINDOW


def is_locked(locked_until: datetime | None, now: datetime) -> bool:
    return locked_until is not None and now < locked_until


def should_lock(recent_failures: int) -> bool:
    return recent_failures >= MAX_FAILURES


def lock_until(now: datetime) -> datetime:
    return now + LOCK_DURATION
