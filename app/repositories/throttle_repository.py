"""Giriş denemesi sınırı kayıtları: başarısız denemeler ve kilitler (e-posta başına)."""

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import LoginFailureRow, LoginLockRow


class SqlThrottleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def locked_until(self, email: str) -> datetime | None:
        row = self._session.get(LoginLockRow, email)
        return row.locked_until if row else None

    def record_failure(self, email: str, at: datetime) -> None:
        self._session.add(LoginFailureRow(email=email, failed_at=at))
        self._session.flush()

    def count_failures_since(self, email: str, since: datetime) -> int:
        query = (
            select(func.count())
            .select_from(LoginFailureRow)
            .where(LoginFailureRow.email == email, LoginFailureRow.failed_at > since)
        )
        return int(self._session.scalar(query) or 0)

    def lock(self, email: str, until: datetime) -> None:
        row = self._session.get(LoginLockRow, email)
        if row is None:
            self._session.add(LoginLockRow(email=email, locked_until=until))
        else:
            row.locked_until = until
        self._session.execute(delete(LoginFailureRow).where(LoginFailureRow.email == email))
        self._session.flush()

    def clear(self, email: str) -> None:
        self._session.execute(delete(LoginFailureRow).where(LoginFailureRow.email == email))
        self._session.execute(delete(LoginLockRow).where(LoginLockRow.email == email))
