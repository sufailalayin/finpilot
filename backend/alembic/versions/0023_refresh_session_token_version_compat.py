"""Backfill refresh session token_version for databases that applied early 0022.

Revision ID: 0023_refresh_session_token_version_compat
Revises: 0022_refresh_sessions
"""

from alembic import op

revision = "0023_refresh_session_token_version_compat"
down_revision = "0022_refresh_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0022 briefly existed without token_version and may already have been
    # applied in production. Keep this migration idempotent so both those
    # databases and fresh installs end up with the same schema.
    op.execute(
        """
        ALTER TABLE refresh_sessions
        ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0
        """
    )


def downgrade() -> None:
    # Do not drop token_version here because fresh databases receive it in
    # 0022 and it is part of the canonical refresh-session schema.
    pass
