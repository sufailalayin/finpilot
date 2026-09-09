import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from app.core.config import get_settings

settings = get_settings()

ANDROID_PUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher"
VALID_STATES = {
    "SUBSCRIPTION_STATE_ACTIVE",
    "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
    "SUBSCRIPTION_STATE_CANCELED",
}


@dataclass
class PlayVerificationResult:
    verified: bool
    product_id: str
    expiry_time: datetime | None
    purchase_state: str


def _parse_rfc3339(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)


def _extract_verification(
    payload: dict,
    *,
    expected_product_id: str,
    now: datetime | None = None,
) -> PlayVerificationResult:
    now = now or datetime.now(timezone.utc)
    state = str(payload.get("subscriptionState") or "UNKNOWN")
    line_items = payload.get("lineItems") or []

    matching_items = [
        item for item in line_items
        if str(item.get("productId") or "") == expected_product_id
    ]

    expiry_candidates = [
        _parse_rfc3339(item.get("expiryTime"))
        for item in matching_items
    ]
    expiry_candidates = [value for value in expiry_candidates if value is not None]
    expiry = max(expiry_candidates) if expiry_candidates else None

    verified = (
        state in VALID_STATES
        and expiry is not None
        and expiry > now
        and bool(matching_items)
    )

    return PlayVerificationResult(
        verified=verified,
        product_id=expected_product_id,
        expiry_time=expiry,
        purchase_state=state,
    )


class GooglePlayVerifier:
    async def _access_token(self) -> str:
        if not settings.google_play_service_account_json:
            raise RuntimeError("Google Play service account is not configured")

        try:
            info = json.loads(settings.google_play_service_account_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Google Play service account JSON is invalid") from exc

        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=[ANDROID_PUBLISHER_SCOPE],
        )

        await asyncio.to_thread(credentials.refresh, Request())
        if not credentials.token:
            raise RuntimeError("Unable to obtain Google Play access token")
        return credentials.token

    async def acknowledge_subscription(
        self,
        product_id: str,
        purchase_token: str,
    ) -> None:
        token = await self._access_token()
        package_name = quote(settings.google_play_package_name, safe="")
        product_id_encoded = quote(product_id, safe="")
        purchase_token_encoded = quote(purchase_token, safe="")
        url = (
            "https://androidpublisher.googleapis.com/androidpublisher/v3/"
            f"applications/{package_name}/purchases/subscriptions/"
            f"{product_id_encoded}/tokens/{purchase_token_encoded}:acknowledge"
        )
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": "Bearer " + token,
                    "Content-Type": "application/json",
                },
                json={},
            )
        if response.status_code not in {200, 409}:
            response.raise_for_status()

    async def verify_subscription(
        self,
        product_id: str,
        purchase_token: str,
    ) -> PlayVerificationResult:
        if not settings.google_play_package_name:
            raise RuntimeError("Google Play package name is not configured")

        token = await self._access_token()
        package_name = quote(settings.google_play_package_name, safe="")
        purchase_token_encoded = quote(purchase_token, safe="")

        url = (
            "https://androidpublisher.googleapis.com/androidpublisher/v3/"
            f"applications/{package_name}/purchases/subscriptionsv2/"
            f"tokens/{purchase_token_encoded}"
        )

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": "Bearer " + token},
            )

        if response.status_code == 404:
            return PlayVerificationResult(
                verified=False,
                product_id=product_id,
                expiry_time=None,
                purchase_state="NOT_FOUND",
            )

        response.raise_for_status()
        return _extract_verification(
            response.json(),
            expected_product_id=product_id,
        )


def get_google_play_verifier() -> GooglePlayVerifier:
    return GooglePlayVerifier()
