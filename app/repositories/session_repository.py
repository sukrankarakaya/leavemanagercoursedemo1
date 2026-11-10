"""Oturumlar — yalnızca oturum kimliğinin SHA-256 özeti saklanır."""

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import SessionRow
from app.domain.sessions import SessionRecord


class SqlSessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: SessionRecord) -> None:
        self._session.add(
            SessionRow(
                token_hash=record.token_hash,
                user_id=record.user_id,
                created_at=record.created_at,
                last_seen_at=record.last_seen_at,
            )
        )
        self._session.flush()

    def get(self, token_hash: str) -> SessionRecord | None:
        row = self._session.get(SessionRow, token_hash)
        if row is None:
            return None
        return SessionRecord(
            token_hash=row.token_hash,
            user_id=row.user_id,
            created_at=row.created_at,
            last_seen_at=row.last_seen_at,
        )

    def touch(self, token_hash: str, now: datetime) -> None:
        row = self._session.get(SessionRow, token_hash)
        if row is not None:
            row.last_seen_at = now
            self._session.flush()

    def delete(self, token_hash: str) -> None:
        self._session.execute(delete(SessionRow).where(SessionRow.token_hash == token_hash))

    def delete_others(self, user_id: str, keep_token_hash: str) -> None:
        self._session.execute(
            delete(SessionRow).where(
                SessionRow.user_id == user_id, SessionRow.token_hash != keep_token_hash
            )
        )

    def count_for_user(self, user_id: str) -> int:
        return len(
            list(self._session.scalars(select(SessionRow).where(SessionRow.user_id == user_id)))
        )
