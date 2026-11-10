"""AC-12 (30 dk hareketsizlik), AC-13 (8 saat mutlak sınır)."""

from datetime import UTC, datetime, timedelta

from app.domain.sessions import SessionRecord, hash_token, is_expired

LOGIN = datetime(2026, 11, 11, 9, 0, tzinfo=UTC)


def _record(last_seen: datetime) -> SessionRecord:
    return SessionRecord(token_hash="h", user_id="u", created_at=LOGIN, last_seen_at=last_seen)


def test_idle_timeout_boundary() -> None:
    record = _record(LOGIN)
    assert not is_expired(record, LOGIN + timedelta(minutes=29, seconds=59))
    assert is_expired(record, LOGIN + timedelta(minutes=30))


def test_absolute_timeout_despite_activity() -> None:
    almost = LOGIN + timedelta(hours=8) - timedelta(seconds=1)
    assert not is_expired(_record(almost), almost)  # her dakika işlem yapılmış gibi
    eight_hours = LOGIN + timedelta(hours=8)
    assert is_expired(_record(eight_hours - timedelta(minutes=1)), eight_hours)


def test_token_hash_is_sha256_hex_and_not_the_token() -> None:
    digest = hash_token("secret-token")
    assert len(digest) == 64
    assert "secret-token" not in digest
    assert hash_token("secret-token") == digest
