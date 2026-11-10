import pytest

from app.domain.clock import FixedClock
from app.domain.errors import DatabaseUnavailableError
from app.services.health_service import HealthService


class ReachableProbe:
    def __init__(self) -> None:
        self.calls = 0

    def ping(self) -> None:
        self.calls += 1


class UnreachableProbe:
    def ping(self) -> None:
        raise DatabaseUnavailableError()


def test_check_ok_uses_clock(fixed_clock: FixedClock) -> None:
    probe = ReachableProbe()
    report = HealthService(probe, fixed_clock).check()
    assert probe.calls == 1
    assert report.database_ok is True
    assert report.server_time == fixed_clock.now()


def test_check_raises_when_db_unreachable(fixed_clock: FixedClock) -> None:
    with pytest.raises(DatabaseUnavailableError) as info:
        HealthService(UnreachableProbe(), fixed_clock).check()
    assert info.value.code == "DB_UNAVAILABLE"
