"""POST /desocupacoes -- validates payload, persists to DynamoDB."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from domain.models import Desocupacao
from domain.validators import ValidationError, validate_desocupacao
from infra import dynamo_repo

from ._common import get_user_sub, json_response, parse_body


def handler(event: dict, _context) -> dict:
    payload = parse_body(event)
    try:
        validated = validate_desocupacao(payload)
    except ValidationError as e:
        return json_response(422, {"errors": e.errors})

    user_sub = get_user_sub(event)
    record = Desocupacao(
        id=str(uuid.uuid4()),
        cidade=validated.cidade,
        edificio=validated.edificio,
        numero_apto=validated.numero_apto,
        area_privativa=validated.area_privativa,
        tipologia=validated.tipologia,
        uso=validated.uso,
        status_evento=validated.status_evento,
        data_evento=validated.data_evento,
        data_inicio_contrato=validated.data_inicio_contrato,
        valor_aluguel=validated.valor_aluguel,
        dias_vacancia=validated.dias_vacancia,
        motivo_desocupacao=validated.motivo_desocupacao,
        mes=validated.mes,
        ano=validated.ano,
        criado_por=user_sub,
        criado_em=datetime.now(timezone.utc).isoformat(),
    )
    dynamo_repo.put(record)

    return json_response(201, record.to_api_dict())
