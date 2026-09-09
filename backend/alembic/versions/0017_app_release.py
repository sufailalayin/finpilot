"""Add app release configuration.

Revision ID: 0017_app_release
Revises: 0016_card_billing
"""

from alembic import op
import sqlalchemy as sa

revision = "0017_app_release"
down_revision = "0016_card_billing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_release",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("latest_version", sa.String(length=40), nullable=False, server_default="1.0.0"),
        sa.Column("latest_build_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("minimum_version", sa.String(length=40), nullable=False, server_default="1.0.0"),
        sa.Column("minimum_build_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("update_url", sa.String(length=1000), nullable=True),
        sa.Column("release_notes", sa.Text(), nullable=True),
        sa.Column("distribution", sa.String(length=30), nullable=False, server_default="apk"),
        sa.Column("is_update_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.execute(
        """
        INSERT INTO app_release
        (id, latest_version, latest_build_number, minimum_version, minimum_build_number, distribution, is_update_enabled)
        VALUES (1, '1.0.0', 1, '1.0.0', 1, 'apk', true)
        """
    )


def downgrade() -> None:
    op.drop_table("app_release")
