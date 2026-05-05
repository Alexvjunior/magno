"""Shared helpers for API Gateway HTTP API Lambda handlers."""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
}


class _DecimalEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if isinstance(o, Decimal):
            f = float(o)
            return int(f) if f.is_integer() else f
        return super().default(o)


def json_response(status: int, body: Any) -> dict:
    return {
        "statusCode": status,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps(body, cls=_DecimalEncoder, ensure_ascii=False),
    }


def parse_body(event: dict) -> dict:
    body = event.get("body") or "{}"
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}


def get_user_sub(event: dict) -> str:
    """Extracts the Cognito user sub from the JWT claims set by API GW authorizer."""
    try:
        return event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    except (KeyError, TypeError):
        return "anonymous"
