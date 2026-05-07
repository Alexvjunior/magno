"""POST /movimentacoes -- validates payload, persists to DynamoDB."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from domain.models import Movimentacao
from domain.validators import ValidationError, validate_movimentacao
from infra import dynamo_repo, google_sheets_repo

from ._common import get_user_sub, json_response, parse_body

LOGGER = logging.getLogger(__name__)


def handler(event: dict, _context) -> dict:
    payload = parse_body(event)
    try:
        validated = validate_movimentacao(payload)
    except ValidationError as e:
        return json_response(422, {"errors": e.errors})

    imovel = dynamo_repo.get_imovel(validated.id_imovel)
    if imovel is None:
        return json_response(
            404,
            {
                "message": "Imovel nao encontrado",
                "idImovel": validated.id_imovel,
            },
        )

    if validated.status_evento == "Locacao":
        try:
            latest = dynamo_repo.latest_movimentacao_for_imovel(validated.id_imovel)
        except Exception as exc:
            LOGGER.exception("Failed to validate latest movimentacao %s in DynamoDB", validated.id_imovel)
            return json_response(
                502,
                {
                    "message": "Falha ao verificar ultimo registro do imovel no DynamoDB",
                    "idImovel": validated.id_imovel,
                    "error": str(exc),
                },
            )

        if latest is None:
            try:
                sheet_status = google_sheets_repo.latest_status_evento_by_imovel(
                    validated.id_imovel
                )
            except Exception as exc:
                LOGGER.exception(
                    "Failed to validate latest movimentacao %s in Google Sheets",
                    validated.id_imovel,
                )
                return json_response(
                    502,
                    {
                        "message": "Falha ao verificar ultimo registro do imovel no Google Sheets",
                        "idImovel": validated.id_imovel,
                        "error": str(exc),
                    },
                )
            latest_is_desocupacao = sheet_status in (None, "Desocupacao")
        else:
            latest_is_desocupacao = latest.status_evento == "Desocupacao"

        if not latest_is_desocupacao:
            return json_response(
                409,
                {
                    "message": "O imovel nao tem como ultimo registro uma desocupacao.",
                    "idImovel": validated.id_imovel,
                },
            )

    user_sub = get_user_sub(event)
    record = Movimentacao(
        id=str(uuid.uuid4()),
        status="ACTIVE",
        id_imovel=imovel.id_imovel,
        cidade=imovel.cidade,
        edificio=imovel.edificio,
        numero_apto=imovel.numero_apto,
        area_privativa=imovel.area_privativa,
        tipologia=imovel.tipologia,
        uso=imovel.uso,
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
    try:
        google_sheets_repo.append_movimentacao(record)
    except Exception as exc:
        LOGGER.exception("Failed to append movimentacao %s to Google Sheets", record.id)
        return json_response(
            502,
            {
                "message": "Movimentacao salva no DynamoDB, mas falhou ao enviar para Google Sheets",
                "dynamoSaved": True,
                "id": record.id,
                "error": str(exc),
            },
        )

    return json_response(201, record.to_api_dict())
