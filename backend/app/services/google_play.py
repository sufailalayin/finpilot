from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import get_settings

settings = get_settings()


@dataclass
class PlayVerificationResult:
    verified: bool
    product_id: str
    expiry_time: datetime | None
    purchase_state: str


class GooglePlayVerifier:
    """
    Google Play subscription verification boundary.

    Production implementation should use the Google Play Developer API
    with a server-side service account. The Android client must never
    decide entitlement state on its own.
    """

    async def verify_subscription(
        self,
        product_id: str,
        purchase_token: str,
    ) -> PlayVerificationResult:
        if not settings.google_play_package_name:
            raise RuntimeError("Google Play verification is not configured")

        # Placeholder boundary until deployment credentials are connected.
        # Never treat this fallback as a verified paid subscription.
        return PlayVerificationResult(
            verified=False,
            product_id=product_id,
            expiry_time=None,
            purchase_state="unverified",
        )


def get_google_play_verifier() -> GooglePlayVerifier:
    return GooglePlayVerifier()
