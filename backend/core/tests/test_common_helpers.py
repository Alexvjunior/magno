import json
from decimal import Decimal

from handlers._common import CORS_HEADERS, get_user_sub, json_response, parse_body


def test_json_response_sets_cors_json_and_encodes_decimal_and_unicode():
    response = json_response(
        200,
        {
            "cidade": "São Paulo",
            "integer": Decimal("10"),
            "decimal": Decimal("10.5"),
        },
    )

    assert response["statusCode"] == 200
    assert response["headers"] == {**CORS_HEADERS, "Content-Type": "application/json"}
    assert "São Paulo" in response["body"]
    assert json.loads(response["body"]) == {
        "cidade": "São Paulo",
        "integer": 10,
        "decimal": 10.5,
    }


def test_parse_body_handles_empty_invalid_and_valid_json():
    assert parse_body({}) == {}
    assert parse_body({"body": ""}) == {}
    assert parse_body({"body": "{invalid"}) == {}
    assert parse_body({"body": '{"ok": true}'}) == {"ok": True}


def test_get_user_sub_reads_cognito_claims_or_falls_back_to_anonymous():
    assert (
        get_user_sub(
            {
                "requestContext": {
                    "authorizer": {"jwt": {"claims": {"sub": "user-123"}}},
                }
            }
        )
        == "user-123"
    )
    assert get_user_sub({}) == "anonymous"
    assert get_user_sub({"requestContext": None}) == "anonymous"

