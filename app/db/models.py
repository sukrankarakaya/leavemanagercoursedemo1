"""SQLAlchemy tabloları (spec 0002). Şema değişikliği yalnızca Alembic migration'ı ile."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, TypeDecorator
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class UTCDateTime(TypeDecorator[datetime]):
    """SQLite saat dilimi saklamaz: UTC'ye çevirip saklar, okurken UTC olarak işaretler."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetime cannot be stored; use an aware UTC datetime")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        assert isinstance(value, datetime)  # noqa: S101 — DateTime impl returns datetime
        return value.replace(tzinfo=UTC)


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    manager_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)


class SessionRow(Base):
    __tablename__ = "sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)


class LoginFailureRow(Base):
    __tablename__ = "login_failures"
    __table_args__ = (Index("ix_login_failures_email_failed_at", "email", "failed_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    failed_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)


class LoginLockRow(Base):
    __tablename__ = "login_locks"

    email: Mapped[str] = mapped_column(String(254), primary_key=True)
    locked_until: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
