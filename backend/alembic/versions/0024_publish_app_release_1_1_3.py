"""Publish FinPilot 1.1.3 build 6 through the app update channel.

Revision ID: 0024_publish_app_release_1_1_3
Revises: 0023_refresh_token_ver
"""

from alembic import op


revision = "0024_publish_app_release_1_1_3"
down_revision = "0023_refresh_token_ver"
branch_labels = None
depends_on = None


UPDATE_URL = (
    "https://finpilot-signed-builder-production.up.railway.app/"
    "FinPilot-1.1.3-build6-production.apk"
)

RELEASE_NOTES = """FinPilot 1.1.3 build 6

- Fixed admin billing-plan creation and manual plan changes.
- Restored decimal/paise display and decimal entry.
- Corrected total balance, liabilities, net worth, savings rate, and financial health calculations.
- Excluded internal transfers from income/expense analytics.
- Includes security hardening that separates customer and administrator login surfaces."""


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE app_release
        SET
            latest_version = '1.1.3',
            latest_build_number = 6,
            update_url = '{UPDATE_URL}',
            release_notes = '{RELEASE_NOTES.replace("'", "''")}',
            distribution = 'apk',
            is_update_enabled = true,
            updated_at = now()
        WHERE id = 1
          AND latest_build_number < 6
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE app_release
        SET
            latest_version = '1.0.0',
            latest_build_number = 1,
            update_url = NULL,
            release_notes = NULL,
            distribution = 'apk',
            is_update_enabled = true,
            updated_at = now()
        WHERE id = 1
          AND latest_version = '1.1.3'
          AND latest_build_number = 6
        """
    )
