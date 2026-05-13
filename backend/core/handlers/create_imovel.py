"""POST /imoveis -- validates payload and persists to DynamoDB."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from domain.models import Imovel
from domain.validators import ValidationError, validate_imovel
from infra import dynamo_repo

from ._common import get_user_sub, json_response, parse_body

LOGGER = logging.getLogger(__name__)


def _duplicate_response(id_imovel: str) -> dict:
    return json_response(
        409,
        {
            "message": "Este imovel ja foi cadastrado.",
            "idImovel": id_imovel,
        },
    )


def handler(event: dict, _context) -> dict:
    payload = parse_body(event)
    try:
        validated = validate_imovel(payload)
    except ValidationError as e:
        return json_response(422, {"errors": e.errors})

    try:
        if dynamo_repo.imovel_exists_by_id(validated.id_imovel):
            return _duplicate_response(validated.id_imovel)
    except Exception as exc:
        LOGGER.exception("Failed to check imovel %s in DynamoDB", validated.id_imovel)
        return json_response(
            502,
            {
                "message": "Falha ao verificar imovel no DynamoDB",
                "idImovel": validated.id_imovel,
                "error": str(exc),
            },
        )

    record = Imovel(
        id_imovel=validated.id_imovel,
        status="ACTIVE",
        cidade=validated.cidade,
        edificio=validated.edificio,
        numero_apto=validated.numero_apto,
        area_privativa=validated.area_privativa,
        tipologia=validated.tipologia,
        uso=validated.uso,
        mobiliado=validated.mobiliado,
        criado_por=get_user_sub(event),
        criado_em=datetime.now(timezone.utc).isoformat(),
    )

    try:
        dynamo_repo.put_imovel(record)
    except dynamo_repo.DuplicateImovelError:
        return _duplicate_response(record.id_imovel)

    return json_response(201, record.to_api_dict())
