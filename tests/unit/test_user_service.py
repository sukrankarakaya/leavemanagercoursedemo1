"""AC-1…AC-5 servis düzeyi: İK kapısı, yönetici kuralları, geçici parola, ilk İK."""

import pytest

from app.domain.errors import EmailTakenError, FirstUserExistsError, ForbiddenError, ValidationError
from app.domain.users import Role, User
from app.services.passwords import Argon2PasswordHasher
from app.services.user_service import UserService


@pytest.fixture
def service(memory_store, fast_hasher: Argon2PasswordHasher, clock) -> UserService:  # type: ignore[no-untyped-def]
    return UserService(memory_store, fast_hasher, clock)


@pytest.fixture
def hr(service: UserService) -> User:
    return service.create_first_hr(email="ik@firma.com", full_name="İK Uzmanı").user


def test_first_hr_only_when_empty(service: UserService) -> None:
    created = service.create_first_hr(email=" IK@Firma.com ", full_name="İK")
    assert created.user.role is Role.HR
    assert created.user.email == "ik@firma.com"
    assert created.user.must_change_password is True
    assert len(created.temp_password) == 12
    with pytest.raises(FirstUserExistsError):
        service.create_first_hr(email="ikinci@firma.com", full_name="İK 2")


def test_manager_rules_by_role(service: UserService, hr: User) -> None:
    manager = service.create_user(
        hr, email="yonetici@firma.com", full_name="Yönetici", role="MANAGER", manager_id=None
    ).user
    service.create_user(hr, email="ik2@firma.com", full_name="İK 2", role="HR", manager_id=None)
    employee = service.create_user(
        hr, email="calisan@firma.com", full_name="Çalışan", role="EMPLOYEE", manager_id=manager.id
    ).user
    assert employee.manager_id == manager.id

    with pytest.raises(ValidationError) as missing:
        service.create_user(
            hr, email="c2@firma.com", full_name="C2", role="EMPLOYEE", manager_id=None
        )
    assert set(missing.value.fields) == {"manager_id"}

    for not_a_manager in (hr.id, employee.id, "yok-boyle-biri"):
        with pytest.raises(ValidationError) as wrong:
            service.create_user(
                hr, email="c3@firma.com", full_name="C3", role="EMPLOYEE", manager_id=not_a_manager
            )
        assert set(wrong.value.fields) == {"manager_id"}


def test_validation_errors_are_collected_per_field(service: UserService, hr: User) -> None:
    with pytest.raises(ValidationError) as info:
        service.create_user(hr, email="bozuk", full_name="  ", role="BOSS", manager_id=None)
    assert set(info.value.fields) == {"email", "full_name", "role"}


def test_duplicate_email_case_insensitive(service: UserService, hr: User) -> None:
    with pytest.raises(EmailTakenError):
        service.create_user(hr, email="IK@FIRMA.COM", full_name="Kopya", role="HR", manager_id=None)


def test_non_hr_cannot_create_or_list(service: UserService, hr: User) -> None:
    manager = service.create_user(
        hr, email="yonetici@firma.com", full_name="Yönetici", role="MANAGER", manager_id=None
    ).user
    with pytest.raises(ForbiddenError):
        service.create_user(manager, email="x@firma.com", full_name="X", role="HR", manager_id=None)
    with pytest.raises(ForbiddenError):
        service.list_users(manager)
    assert {u.email for u in service.list_users(hr)} == {"ik@firma.com", "yonetici@firma.com"}


def test_temp_password_is_stored_only_as_argon2id_hash(
    service: UserService,
    memory_store,
    fast_hasher: Argon2PasswordHasher,  # type: ignore[no-untyped-def]
) -> None:
    created = service.create_first_hr(email="ik@firma.com", full_name="İK")
    _, stored = memory_store.state.users[created.user.id]
    assert stored.startswith("$argon2id$")
    assert created.temp_password not in stored
    assert fast_hasher.verify(stored, created.temp_password)
