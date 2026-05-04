"""DynamoDB repository for the single-table `desocupacoes` schema.

Schema:
- PK: TENANT#<tenant_id>          (single-tenant for now: "default")
- SK: DESOC#<dataEvento>#<id>
- GSI1PK: ANO_MES#<yyyy-mm>
- GSI1SK: <dataEvento ISO>
"""
from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from typing import Any, Iterable

import boto3
from boto3.dynamodb.conditions import Key

from domain.models import Desocupacao

TABLE_NAME = os.environ.get("DDB_TABLE", "claud-desocupacoes")
TENANT_ID = "default"
DEFAULT_TEXT = "Nao informado"

_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(TABLE_NAME)


def _to_decimal(value: float | int) -> Decimal:
    return Decimal(str(value))


def _to_item(d: Desocupacao) -> dict:
    yyyy_mm = f"{d.ano:04d}-{d.mes:02d}"
    data_evento = d.data_evento.isoformat()
    return {
        "PK": f"TENANT#{TENANT_ID}",
        "SK": f"DESOC#{data_evento}#{d.id}",
        "GSI1PK": f"ANO_MES#{yyyy_mm}",
        "GSI1SK": data_evento,
        "id": d.id,
        "cidade": d.cidade,
        "edificio": d.edificio,
        "numeroApto": d.numero_apto,
        "areaPrivativa": _to_decimal(d.area_privativa),
        "tipologia": d.tipologia,
        "uso": d.uso,
        "statusEvento": d.status_evento,
        "dataEvento": data_evento,
        "dataInicioContrato": d.data_inicio_contrato.isoformat(),
        "valorAluguel": _to_decimal(d.valor_aluguel),
        "diasVacancia": d.dias_vacancia,
        "motivoDesocupacao": d.motivo_desocupacao,
        "mes": d.mes,
        "ano": d.ano,
        "criadoPor": d.criado_por,
        "criadoEm": d.criado_em,
    }


def _text(value: Any, default: str = DEFAULT_TEXT) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _date(value: Any, default: date | None = None) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return default or date(1970, 1, 1)


def _uso(value: Any) -> str:
    return value if value in {"Residencial", "Comercial"} else "Residencial"


def _from_item(item: dict) -> Desocupacao:
    data_evento = _date(item.get("dataEvento", item.get("dataFim")))
    data_inicio_contrato = _date(
        item.get("dataInicioContrato", item.get("dataInicio")),
        default=data_evento,
    )
    mes = _int(item.get("mes"), data_evento.month)
    ano = _int(item.get("ano"), data_evento.year)

    return Desocupacao(
        id=_text(item.get("id"), "sem-id"),
        cidade=_text(item.get("cidade")),
        edificio=_text(item.get("edificio", item.get("empreendimento"))),
        numero_apto=_text(item.get("numeroApto", item.get("apartamento"))),
        area_privativa=_float(item.get("areaPrivativa")),
        tipologia=_text(item.get("tipologia")),
        uso=_uso(item.get("uso")),
        status_evento=_text(item.get("statusEvento"), "Legado"),
        data_evento=data_evento,
        data_inicio_contrato=data_inicio_contrato,
        valor_aluguel=_float(item.get("valorAluguel")),
        dias_vacancia=_int(item.get("diasVacancia")),
        motivo_desocupacao=_text(item.get("motivoDesocupacao")),
        mes=mes,
        ano=ano,
        criado_por=_text(item.get("criadoPor"), "legacy"),
        criado_em=_text(item.get("criadoEm"), "1970-01-01T00:00:00Z"),
    )


def put(d: Desocupacao) -> None:
    _table.put_item(Item=_to_item(d))


def list_by_month(year: int, month: int) -> list[Desocupacao]:
    yyyy_mm = f"{year:04d}-{month:02d}"
    resp = _table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"ANO_MES#{yyyy_mm}"),
    )
    return [_from_item(i) for i in resp.get("Items", [])]


def list_all(limit: int = 200) -> list[Desocupacao]:
    resp = _table.query(
        KeyConditionExpression=Key("PK").eq(f"TENANT#{TENANT_ID}"),
        ScanIndexForward=False,
        Limit=limit,
    )
    return [_from_item(i) for i in resp.get("Items", [])]


def list_all_pages() -> Iterable[Desocupacao]:
    last = None
    while True:
        kwargs = {
            "KeyConditionExpression": Key("PK").eq(f"TENANT#{TENANT_ID}"),
            "ScanIndexForward": False,
        }
        if last:
            kwargs["ExclusiveStartKey"] = last
        resp = _table.query(**kwargs)
        for i in resp.get("Items", []):
            yield _from_item(i)
        last = resp.get("LastEvaluatedKey")
        if not last:
            break
