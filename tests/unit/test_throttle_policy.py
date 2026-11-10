"""AC-17, AC-18: giriş denemesi sınırının kural katmanı (servis/integration testleri ayrıca)."""

from datetime import UTC, datetime, timedelta

from app.domain.throttle import is_locked, lock_until, should_lock, window_start

NOW = datetime(2026, 11, 11, 9, 0, tzinfo=UTC)


def test_fifth_failure_locks() -> None:
    assert not should_lock(4)
    assert should_lock(5)
    assert lock_until(NOW) == NOW + timedelta(minutes=15)


def test_lock_expires_and_old_failures_ignored() -> None:
    until = lock_until(NOW)
    assert is_locked(until, NOW + timedelta(minutes=14, seconds=59))
    assert not is_locked(until, NOW + timedelta(minutes=15))
    assert not is_locked(None, NOW)
    assert window_start(NOW) == NOW - timedelta(minutes=15)
