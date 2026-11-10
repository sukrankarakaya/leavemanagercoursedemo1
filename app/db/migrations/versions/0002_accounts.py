"""accounts — kullanıcılar, oturumlar, giriş denemesi sınırı (spec 0002)

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("manager_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_table(
        "login_failures",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("failed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_login_failures_email_failed_at", "login_failures", ["email", "failed_at"])
    op.create_table(
        "login_locks",
        sa.Column("email", sa.String(254), primary_key=True),
        sa.Column("locked_until", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("login_locks")
    op.drop_index("ix_login_failures_email_failed_at", table_name="login_failures")
    op.drop_table("login_failures")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("users")
