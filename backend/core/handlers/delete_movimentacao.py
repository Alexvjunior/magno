"""DELETE /movimentacoes/{id}?dataEvento= -- marks a record as deleted."""
from __future__ import annotations

import logging
from datetime import date

from infra import dynamo_repo, google_sheets_repo

from ._common import json_response

LOGGER = logging.getLogger(__name__)


def handler(event: dict, _context) -> dict:
    record_id = (event.get("pathParameters") or {}).get("id", "").strip()
    data_evento_raw = (event.get("queryStringParameters") or {}).get("dataEvento", "").strip()

    if not record_id:
        return json_response(400, {"errors": {"id": "id obrigatorio"}})

    try:
        data_evento = date.fromisoformat(data_evento_raw)
    except ValueError:
        return json_response(400, {"errors": {"dataEvento": "dataEvento invalida"}})

    record = dynamo_repo.get(record_id, data_evento)
    if record is None:
        return json_response(404, {"message": "Movimentacao nao encontrada"})

    deleted = dynamo_repo.mark_deleted(record_id, data_evento)
    if not deleted:
        return json_response(404, {"message": "Movimentacao nao encontrada"})

    try:
        sheets_deleted = google_sheets_repo.delete_movimentacao_by_imovel_and_date(
            record.id_imovel,
            record.data_evento,
        )
    except Exception as exc:
        LOGGER.exception("Failed to delete movimentacao %s from Google Sheets", record_id)
        return json_response(
            502,
            {
                "message": "Movimentacao removida no DynamoDB, mas falhou ao remover do Google Sheets",
                "dynamoDeleted": True,
                "id": record_id,
                "error": str(exc),
            },
        )

    return json_response(200, {"id": record_id, "status": "DELETED", "sheetsDeleted": sheets_deleted})
