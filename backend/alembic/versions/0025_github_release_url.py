"""Point FinPilot 1.1.3 build 6 updates at durable GitHub Release assets.

Revision ID: 0025_github_release_url
Revises: 0024_publish_app_release_1_1_3
"""

from alembic import op


revision = "0025_github_release_url"
down_revision = "0024_publish_app_release_1_1_3"
branch_labels = None
depends_on = None


OLD_UPDATE_URL = (
    "https://finpilot-signed-builder-production.up.railway.app/"
    "FinPilot-1.1.3-build6-production.apk"
)
NEW_UPDATE_URL = (
    "https://github.com/sufailalayin/finpilot/releases/download/"
    "v1.1.3-build6/FinPilot-1.1.3-build6-production.apk"
)


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE app_release
        SET
            update_url = '{NEW_UPDATE_URL}',
            updated_at = now()
        WHERE id = 1
          AND latest_version = '1.1.3'
          AND latest_build_number = 6
          AND (
              update_url IS NULL
              OR update_url = '{OLD_UPDATE_URL}'
          )
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE app_release
        SET
            update_url = '{OLD_UPDATE_URL}',
            updated_at = now()
        WHERE id = 1
          AND latest_version = '1.1.3'
          AND latest_build_number = 6
          AND update_url = '{NEW_UPDATE_URL}'
        """
    )
