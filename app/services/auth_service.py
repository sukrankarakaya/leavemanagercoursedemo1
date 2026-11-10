"""Giriş, çıkış, oturum doğrulama, parola değiştirme (spec 0002, R-5…R-10)."""

import secrets
from collections.abc import Callable
from dataclasses import dataclass

from app.domain import throttle
from app.domain.clock import Clock
from app.domain.errors import (
    InvalidCredentialsError,
    SessionExpiredError,
    UnauthenticatedError,
    ValidationError,
)
from app.domain.sessions import SessionRecord, hash_token, is_expired
from app.domain.users import User, validate_new_password
from app.services.passwords import PasswordHasher
from app.services.ports import UnitOfWorkFactory


def _new_token() -> str:
    return secrets.token_urlsafe(32)


@dataclass(frozen=True)
class LoginResult:
    token: str
    user: User


@dataclass(frozen=True)
class AuthContext:
    user: User
    token_hash: str


class AuthService:
    def __init__(
        self,
        uow: UnitOfWorkFactory,
        hasher: PasswordHasher,
        clock: Clock,
        token_factory: Callable[[], str] = _new_token,
    ) -> None:
        self._uow = uow
        self._hasher = hasher
        self._clock = clock
        self._new_token = token_factory

    def login(self, email: str, password: str, previous_token: str | None = None) -> LoginResult:
        """Başarısızlıkta hep InvalidCredentialsError (hatalı / yok / kilitli ayırt edilmez)."""
        email = email.strip().lower()
        now = self._clock.now()
        failed = False
        with self._uow() as uow:
            if throttle.is_locked(uow.throttle.locked_until(email), now):
                self._hasher.dummy_verify(password)
                failed = True
                user = None
            else:
                credentials = uow.users.get_credentials(email)
                if credentials is None:
                    self._hasher.dummy_verify(password)
                    user = None
                else:
                    user = credentials[0] if self._hasher.verify(credentials[1], password) else None
                if user is None:
                    failed = True
                    # Sayım ve kilit aynı transaction'da: eşzamanlı denemeler sayımdan kaçmaz.
                    uow.throttle.record_failure(email, now)
                    recent = uow.throttle.count_failures_since(email, throttle.window_start(now))
                    if throttle.should_lock(recent):
                        uow.throttle.lock(email, throttle.lock_until(now))
            if user is not None:
                uow.throttle.clear(email)
                if previous_token:
                    uow.sessions.delete(hash_token(previous_token))  # oturum kimliği yenilenir
                token = self._new_token()
                uow.sessions.add(SessionRecord(hash_token(token), user.id, now, now))
        if failed or user is None:
            raise InvalidCredentialsError()
        return LoginResult(token=token, user=user)

    def authenticate(self, token: str | None) -> AuthContext:
        """Geçerli oturumu döner ve hareket zamanını günceller."""
        if not token:
            raise UnauthenticatedError()
        token_hash = hash_token(token)
        now = self._clock.now()
        expired = False
        with self._uow() as uow:
            record = uow.sessions.get(token_hash)
            if record is None:
                raise UnauthenticatedError()
            user = uow.users.get_by_id(record.user_id)
            if is_expired(record, now) or user is None:
                uow.sessions.delete(token_hash)
                expired = user is not None
            else:
                uow.sessions.touch(token_hash, now)
        if expired:
            raise SessionExpiredError()
        if user is None:
            raise UnauthenticatedError()
        return AuthContext(user=user, token_hash=token_hash)

    def logout(self, token: str | None) -> None:
        if not token:
            return
        with self._uow() as uow:
            uow.sessions.delete(hash_token(token))

    def change_password(
        self, context: AuthContext, current_password: str, new_password: str
    ) -> None:
        with self._uow() as uow:
            credentials = uow.users.get_credentials(context.user.email)
            if credentials is None or not self._hasher.verify(credentials[1], current_password):
                raise ValidationError({"current_password": "Mevcut parola hatalı."})
            validate_new_password(
                new_password, email=context.user.email, current_password=current_password
            )
            uow.users.update_password(context.user.id, self._hasher.hash(new_password))
            # Aynı transaction'da: diğer oturumlar kapanır, değiştiren oturum kalır (R-8).
            uow.sessions.delete_others(context.user.id, context.token_hash)
