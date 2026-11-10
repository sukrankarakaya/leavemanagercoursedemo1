"""Hesap oluşturma ve listeleme — yalnızca İK; ilk İK hesabı (spec 0002, R-1…R-4)."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass

from app.domain.clock import Clock
from app.domain.errors import EmailTakenError, FirstUserExistsError, ForbiddenError, ValidationError
from app.domain.users import (
    Role,
    User,
    generate_temp_password,
    normalize_email,
    normalize_full_name,
    validate_manager,
)
from app.services.passwords import PasswordHasher
from app.services.ports import UnitOfWork, UnitOfWorkFactory


@dataclass(frozen=True)
class CreatedUser:
    user: User
    temp_password: str  # yalnızca bu yanıtta, bir kez (R-3)


def _require_hr(actor: User) -> None:
    if actor.role is not Role.HR:
        raise ForbiddenError()


class UserService:
    def __init__(
        self,
        uow: UnitOfWorkFactory,
        hasher: PasswordHasher,
        clock: Clock,
        id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
        password_factory: Callable[[], str] = generate_temp_password,
    ) -> None:
        self._uow = uow
        self._hasher = hasher
        self._clock = clock
        self._new_id = id_factory
        self._new_password = password_factory

    def create_user(
        self, actor: User, *, email: str, full_name: str, role: str, manager_id: str | None
    ) -> CreatedUser:
        _require_hr(actor)
        with self._uow() as uow:
            return self._create(
                uow, email=email, full_name=full_name, role=role, manager_id=manager_id
            )

    def list_users(self, actor: User) -> list[User]:
        _require_hr(actor)
        with self._uow() as uow:
            return uow.users.list_all()

    def create_first_hr(self, *, email: str, full_name: str) -> CreatedUser:
        with self._uow() as uow:
            if uow.users.count() > 0:
                raise FirstUserExistsError()
            return self._create(
                uow, email=email, full_name=full_name, role=Role.HR, manager_id=None
            )

    def _create(
        self, uow: UnitOfWork, *, email: str, full_name: str, role: str, manager_id: str | None
    ) -> CreatedUser:
        errors: dict[str, str] = {}
        clean_email = clean_name = ""
        parsed_role: Role | None = None
        try:
            clean_email = normalize_email(email)
        except ValidationError as exc:
            errors.update(exc.fields)
        try:
            clean_name = normalize_full_name(full_name)
        except ValidationError as exc:
            errors.update(exc.fields)
        try:
            parsed_role = Role(role)
        except ValueError:
            errors["role"] = "Rol Çalışan, Yönetici veya İK olmalıdır."
        if parsed_role is not None:
            manager = uow.users.get_by_id(manager_id) if manager_id else None
            try:
                validate_manager(parsed_role, manager, manager_requested=bool(manager_id))
            except ValidationError as exc:
                errors.update(exc.fields)
        if errors:
            raise ValidationError(errors)
        assert parsed_role is not None  # noqa: S101 — no errors means role parsed
        if uow.users.get_credentials(clean_email) is not None:
            raise EmailTakenError()
        temp_password = self._new_password()
        user = User(
            id=self._new_id(),
            email=clean_email,
            full_name=clean_name,
            role=parsed_role,
            manager_id=manager_id or None,
            must_change_password=True,
            created_at=self._clock.now(),
        )
        uow.users.add(user, self._hasher.hash(temp_password))
        return CreatedUser(user=user, temp_password=temp_password)
