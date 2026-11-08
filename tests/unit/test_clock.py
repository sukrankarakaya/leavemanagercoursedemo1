from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from app.domain.clock import FixedClock, SystemClock


def test_fixed_clock_returns_its_moment_and_date() -> None:
    moment = datetime(2026, 11, 8, 23, 59, tzinfo=UTC)
    clock = FixedClock(moment)
    assert clock.now() == moment
    assert clock.today() == date(2026, 11, 8)


def test_fixed_clock_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        FixedClock(datetime(2026, 11, 8, 9, 30))  # noqa: DTZ001 — naive on purpose


def test_fixed_clock_rejects_non_utc_offset() -> None:
    with pytest.raises(ValueError):
        FixedClock(datetime(2026, 11, 8, 9, 30, tzinfo=timezone(timedelta(hours=3))))


def test_system_clock_is_timezone_aware_utc() -> None:
    now = SystemClock().now()
    assert now.utcoffset() == timedelta(0)
    assert SystemClock().today() in {now.date(), now.date() + timedelta(days=1)}
