"""Ortak test fixture'ları: sabit/ilerletilebilir saat, test başına geçici veritabanı,
düşük maliyetli Argon2 ve bellek içi unit of work (docs/testing.md)."""

import copy
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import TracebackType
from typing import Self

import pytest

from app.domain.clock import FixedClock
from app.domain.errors import EmailTakenError
from app.domain.sessions import SessionRecord
from app.domain.users import User
from app.services.passwords import Argon2PasswordHasher

FIXED_NOW = datetime(2026, 11, 8, 9, 30, tzinfo=UTC)


@pytest.fixture
def fixed_clock() -> FixedClock:
    return FixedClock(FIXED_NOW)


class MutableClock:
    """Testte zamanı ileri saran saat (oturum ve giriş sınırı süreleri)."""

    def __init__(self, start: datetime = FIXED_NOW) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def today(self) -> date:
        return self._now.date()

    def advance(self, **delta: float) -> None:
        self._now += timedelta(**delta)


@pytest.fixture
def clock() -> MutableClock:
    return MutableClock()


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    """Bu teste özel, test bitince silinen SQLite dosyası."""
    return f"sqlite:///{(tmp_path / 'test.db').as_posix()}"


@pytest.fixture(scope="session")
def fast_hasher() -> Argon2PasswordHasher:
    """Algoritma yine argon2id; yalnızca maliyet düşük (test hızı)."""
    return Argon2PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1)


# --- bellek içi unit of work (servis unit testleri) -------------------------------------------


@dataclass
class MemoryState:
    users: dict[str, tuple[User, str]] = field(default_factory=dict)
    sessions: dict[str, SessionRecord] = field(default_factory=dict)
    failures: list[tuple[str, datetime]] = field(default_factory=list)
    locks: dict[str, datetime] = field(default_factory=dict)


class MemoryUsers:
    def __init__(self, state: MemoryState) -> None:
        self.s = state

    def count(self) -> int:
        return len(self.s.users)

    def get_by_id(self, user_id: str) -> User | None:
        entry = self.s.users.get(user_id)
        return entry[0] if entry else None

    def get_credentials(self, email: str) -> tuple[User, str] | None:
        return next((e for e in self.s.users.values() if e[0].email == email), None)

    def add(self, user: User, password_hash: str) -> None:
        if self.get_credentials(user.email) is not None:
            raise EmailTakenError()
        self.s.users[user.id] = (user, password_hash)

    def update_password(self, user_id: str, password_hash: str) -> None:
        user, _ = self.s.users[user_id]
        self.s.users[user_id] = (replace(user, must_change_password=False), password_hash)

    def list_all(self) -> list[User]:
        return sorted((e[0] for e in self.s.users.values()), key=lambda u: (u.full_name, u.email))


class MemorySessions:
    def __init__(self, state: MemoryState) -> None:
        self.s = state

    def add(self, record: SessionRecord) -> None:
        self.s.sessions[record.token_hash] = record

    def get(self, token_hash: str) -> SessionRecord | None:
        return self.s.sessions.get(token_hash)

    def touch(self, token_hash: str, now: datetime) -> None:
        if token_hash in self.s.sessions:
            self.s.sessions[token_hash] = replace(self.s.sessions[token_hash], last_seen_at=now)

    def delete(self, token_hash: str) -> None:
        self.s.sessions.pop(token_hash, None)

    def delete_others(self, user_id: str, keep_token_hash: str) -> None:
        for key in [
            k for k, r in self.s.sessions.items() if r.user_id == user_id and k != keep_token_hash
        ]:
            del self.s.sessions[key]


class MemoryThrottle:
    def __init__(self, state: MemoryState) -> None:
        self.s = state

    def locked_until(self, email: str) -> datetime | None:
        return self.s.locks.get(email)

    def record_failure(self, email: str, at: datetime) -> None:
        self.s.failures.append((email, at))

    def count_failures_since(self, email: str, since: datetime) -> int:
        return sum(1 for e, at in self.s.failures if e == email and at > since)

    def lock(self, email: str, until: datetime) -> None:
        self.s.locks[email] = until
        self.s.failures = [f for f in self.s.failures if f[0] != email]

    def clear(self, email: str) -> None:
        self.s.locks.pop(email, None)
        self.s.failures = [f for f in self.s.failures if f[0] != email]


class MemoryUnitOfWork:
    """Gerçek UoW gibi: başarıda değişiklikler kalır, istisnada geri alınır."""

    def __init__(self, store: "MemoryStore") -> None:
        self._store = store

    def __enter__(self) -> Self:
        self._work = copy.deepcopy(self._store.state)
        self.users = MemoryUsers(self._work)
        self.sessions = MemorySessions(self._work)
        self.throttle = MemoryThrottle(self._work)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self._store.state = self._work


class MemoryStore:
    def __init__(self) -> None:
        self.state = MemoryState()

    def __call__(self) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self)


@pytest.fixture
def memory_store() -> MemoryStore:
    return MemoryStore()
