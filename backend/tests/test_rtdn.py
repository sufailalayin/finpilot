import base64
import json


def encode_rtdn(payload: dict) -> str:
    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")


def test_rtdn_payload_encoding_round_trip():
    payload = {
        "version": "1.0",
        "packageName": "com.hastronventures.finpilot",
        "subscriptionNotification": {
            "version": "1.0",
            "notificationType": 2,
            "purchaseToken": "token-123",
        },
    }
    encoded = encode_rtdn(payload)
    decoded = json.loads(base64.b64decode(encoded).decode("utf-8"))
    assert decoded["subscriptionNotification"]["purchaseToken"] == "token-123"
