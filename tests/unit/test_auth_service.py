"""Giriş, oturum, parola değiştirme ve sınır — servis düzeyi (bellek içi UoW, sabit saat)."""

import pytest

from app.domain.errors import (
    InvalidCredentialsError,
    SessionExpiredError,
    UnauthenticatedError,
    ValidationError,
)
from app.domain.sessions import hash_token
from app.services.auth_service import AuthService
from app.services.passwords import Argon2PasswordHasher
from app.services.user_service import UserService

PASSWORD = "cok guzel bir parola"


@pytest.fixture
def auth(memory_store, fast_hasher: Argon2PasswordHasher, clock) -> AuthService:  # type: ignore[no-untyped-def]
    return AuthService(memory_store, fast_hasher, clock)


@pytest.fixture
def temp_password(memory_store, fast_hasher: Argon2PasswordHasher, clock) -> str:  # type: ignore[no-untyped-def]
    return (
        UserService(memory_store, fast_hasher, clock)
        .create_first_hr(email="ik@firma.com", full_name="İK")
        .temp_password
    )


def test_login_and_authenticate(auth: AuthService, temp_password: str, memory_store) -> None:  # type: ignore[no-untyped-def]
    result = auth.login("IK@firma.com", temp_password)
    assert auth.authenticate(result.token).user.email == "ik@firma.com"
    assert result.token not in memory_store.state.sessions  # yalnızca özet saklanır
    assert hash_token(result.token) in memory_store.state.sessions


def test_wrong_and_unknown_raise_the_same_error(auth: AuthService, temp_password: str) -> None:
    with pytest.raises(InvalidCredentialsError):
        auth.login("ik@firma.com", "yanlis parola!!")
    with pytest.raises(InvalidCredentialsError):
        auth.login("yok@firma.com", temp_password)


def test_fifth_failure_locks_even_correct_password(
    auth: AuthService,
    temp_password: str,
    clock,  # type: ignore[no-untyped-def]
) -> None:
    for _ in range(4):
        with pytest.raises(InvalidCredentialsError):
            auth.login("ik@firma.com", "yanlis parola!!")
    auth.login("ik@firma.com", temp_password)  # 4 sonra doğru → kabul, sayaç sıfır
    for _ in range(5):
        with pytest.raises(InvalidCredentialsError):
            auth.login("ik@firma.com", "yanlis parola!!")
    with pytest.raises(InvalidCredentialsError):
        auth.login("ik@firma.com", temp_password)
    clock.advance(minutes=15)
    auth.login("ik@firma.com", temp_password)


def test_old_failures_fall_out_of_the_window(
    auth: AuthService,
    temp_password: str,
    clock,  # type: ignore[no-untyped-def]
) -> None:
    for _ in range(4):
        with pytest.raises(InvalidCredentialsError):
            auth.login("ik@firma.com", "yanlis parola!!")
    clock.advance(minutes=15, seconds=1)
    with pytest.raises(InvalidCredentialsError):
        auth.login("ik@firma.com", "yanlis parola!!")  # pencerede yalnızca 1
    auth.login("ik@firma.com", temp_password)


def test_idle_and_absolute_expiry(auth: AuthService, temp_password: str, clock) -> None:  # type: ignore[no-untyped-def]
    token = auth.login("ik@firma.com", temp_password).token
    clock.advance(minutes=29, seconds=59)
    auth.authenticate(token)
    clock.advance(minutes=30)
    with pytest.raises(SessionExpiredError):
        auth.authenticate(token)
    with pytest.raises(UnauthenticatedError):
        auth.authenticate(token)  # süresi dolan oturum silindi

    token = auth.login("ik@firma.com", temp_password).token
    for _ in range(16):  # 8 saat boyunca her 30 dakikadan önce işlem
        clock.advance(minutes=29, seconds=59)
        if _ < 16 - 1:
            auth.authenticate(token)
    clock.advance(seconds=16)
    with pytest.raises(SessionExpiredError):
        auth.authenticate(token)


def test_change_password_revokes_other_sessions_and_needs_current(
    auth: AuthService, temp_password: str
) -> None:
    first = auth.login("ik@firma.com", temp_password).token
    second = auth.login("ik@firma.com", temp_password).token
    context = auth.authenticate(first)
    with pytest.raises(ValidationError) as wrong:
        auth.change_password(context, "yanlis mevcut", PASSWORD)
    assert set(wrong.value.fields) == {"current_password"}
    auth.change_password(context, temp_password, PASSWORD)
    assert auth.authenticate(first).user.must_change_password is False
    with pytest.raises(UnauthenticatedError):
        auth.authenticate(second)
    auth.login("ik@firma.com", PASSWORD)


def test_login_rotates_previous_session(auth: AuthService, temp_password: str) -> None:
    old = auth.login("ik@firma.com", temp_password).token
    new = auth.login("ik@firma.com", temp_password, previous_token=old).token
    assert new != old
    with pytest.raises(UnauthenticatedError):
        auth.authenticate(old)
    auth.logout(new)
    with pytest.raises(UnauthenticatedError):
        auth.authenticate(new)
