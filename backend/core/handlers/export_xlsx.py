"""GET /desocupacoes/export -- generates an XLSX and returns a presigned S3 URL."""
from __future__ import annotations

from datetime import datetime, timezone

from domain.xlsx_writer import build_xlsx
from infra import dynamo_repo, s3_client

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
        scope = f"{int(ano):04d}-{int(mes):02d}"
    else:
        items = list(dynamo_repo.list_all_pages())
        scope = "all"

    data = build_xlsx(items)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"exports/{scope}/{stamp}.xlsx"
    s3_client.upload_xlsx(key, data)
    url = s3_client.presigned_get(key)

    return json_response(
        200,
        {
            "url": url,
            "filename": f"desocupacoes-{scope}-{stamp}.xlsx",
            "count": len(items),
        },
    )
