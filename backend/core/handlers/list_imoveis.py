"""GET /imoveis -- lists imovel records."""
from __future__ import annotations

from infra import dynamo_repo

from ._common import json_response


def handler(_event: dict, _context) -> dict:
    items = dynamo_repo.list_imoveis(limit=200)
    return json_response(200, [item.to_api_dict() for item in items])
