from datetime import datetime, timedelta, timezone

from app.services.google_play import _extract_verification


def test_active_matching_subscription_is_verified():
    now = datetime.now(timezone.utc)
    expiry = (now + timedelta(days=30)).isoformat().replace("+00:00", "Z")

    result = _extract_verification(
        {
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "lineItems": [
                {
                    "productId": "finpilot_pro_monthly",
                    "expiryTime": expiry,
                }
            ],
        },
        expected_product_id="finpilot_pro_monthly",
        now=now,
    )

    assert result.verified is True
    assert result.expiry_time is not None


def test_wrong_product_is_rejected():
    now = datetime.now(timezone.utc)
    expiry = (now + timedelta(days=30)).isoformat().replace("+00:00", "Z")

    result = _extract_verification(
        {
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "lineItems": [
                {
                    "productId": "other_product",
                    "expiryTime": expiry,
                }
            ],
        },
        expected_product_id="finpilot_pro_monthly",
        now=now,
    )

    assert result.verified is False


def test_expired_subscription_is_rejected():
    now = datetime.now(timezone.utc)
    expiry = (now - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")

    result = _extract_verification(
        {
            "subscriptionState": "SUBSCRIPTION_STATE_EXPIRED",
            "lineItems": [
                {
                    "productId": "finpilot_pro_monthly",
                    "expiryTime": expiry,
                }
            ],
        },
        expected_product_id="finpilot_pro_monthly",
        now=now,
    )

    assert result.verified is False
