from app.core.security import create_access_token, decode_access_token_claims


def test_access_token_preserves_session_version():
    token = create_access_token("00000000-0000-0000-0000-000000000001", token_version=7)
    claims = decode_access_token_claims(token)

    assert claims is not None
    assert claims["sub"] == "00000000-0000-0000-0000-000000000001"
    assert claims["ver"] == 7


def test_legacy_default_token_version_is_zero():
    token = create_access_token("user-123")
    claims = decode_access_token_claims(token)

    assert claims is not None
    assert claims["ver"] == 0
