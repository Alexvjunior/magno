"""GET /desocupacoes?ano=&mes= -- lists records."""
from __future__ import annotations

from infra import dynamo_repo

from ._common import json_response


def handler(event: dict, _context) -> dict:
    qs = event.get("queryStringParameters") or {}
    ano = qs.get("ano")
    mes = qs.get("mes")

    if ano and mes:
        try:
            items = dynamo_repo.list_by_month(int(ano), int(mes))
        except ValueError:
            return json_response(400, {"errors": {"ano": "ano/mes inválidos"}})
    else:
        items = dynamo_repo.list_all(limit=200)

    return json_response(200, [d.to_api_dict() for d in items])
