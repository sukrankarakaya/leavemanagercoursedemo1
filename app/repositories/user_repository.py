"""Kullanıcı hesapları (services.ports.UserRepository uygulaması)."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import UserRow
from app.domain.errors import EmailTakenError
from app.domain.users import Role, User


def _to_user(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        full_name=row.full_name,
        role=Role(row.role),
        manager_id=row.manager_id,
        must_change_password=row.must_change_password,
        created_at=row.created_at,
    )


class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def count(self) -> int:
        return int(self._session.scalar(select(func.count()).select_from(UserRow)) or 0)

    def get_by_id(self, user_id: str) -> User | None:
        row = self._session.get(UserRow, user_id)
        return _to_user(row) if row else None

    def get_credentials(self, email: str) -> tuple[User, str] | None:
        row = self._session.scalar(select(UserRow).where(UserRow.email == email))
        return (_to_user(row), row.password_hash) if row else None

    def add(self, user: User, password_hash: str) -> None:
        self._session.add(
            UserRow(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                manager_id=user.manager_id,
                password_hash=password_hash,
                must_change_password=user.must_change_password,
                created_at=user.created_at,
            )
        )
        try:
            self._session.flush()
        except IntegrityError as exc:
            # The email pre-check in the service runs first; this covers a concurrent insert.
            raise EmailTakenError() from exc

    def update_password(self, user_id: str, password_hash: str) -> None:
        row = self._session.get(UserRow, user_id)
        if row is None:
            raise LookupError(user_id)
        row.password_hash = password_hash
        row.must_change_password = False
        self._session.flush()

    def list_all(self) -> list[User]:
        rows = self._session.scalars(select(UserRow).order_by(UserRow.full_name, UserRow.email))
        return [_to_user(row) for row in rows]
