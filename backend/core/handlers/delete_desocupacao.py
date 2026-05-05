"""DELETE /desocupacoes/{id}?dataEvento= -- marks a record as deleted."""
from __future__ import annotations

from datetime import date

from infra import dynamo_repo

from ._common import json_response


def handler(event: dict, _context) -> dict:
    record_id = (event.get("pathParameters") or {}).get("id", "").strip()
    data_evento_raw = (event.get("queryStringParameters") or {}).get("dataEvento", "").strip()

    if not record_id:
        return json_response(400, {"errors": {"id": "id obrigatorio"}})

    try:
        data_evento = date.fromisoformat(data_evento_raw)
    except ValueError:
        return json_response(400, {"errors": {"dataEvento": "dataEvento invalida"}})

    deleted = dynamo_repo.mark_deleted(record_id, data_evento)
    if not deleted:
        return json_response(404, {"message": "Desocupacao nao encontrada"})

    return json_response(200, {"id": record_id, "status": "DELETED"})
