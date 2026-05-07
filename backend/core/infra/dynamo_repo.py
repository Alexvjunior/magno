"""DynamoDB repository for the single-table registros schema.

Schema:
- PK: TENANT#<tenant_id>          (single-tenant for now: "default")
- SK: MOV#<dataEvento>#<id>
- GSI1PK: ANO_MES#<yyyy-mm>
- GSI1SK: <dataEvento ISO>
- GSI2PK: STATUS#<ACTIVE|DELETED>
- GSI2SK: <dataEvento ISO>#<id>
"""
from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from typing import Any, Iterable

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from domain.models import Imovel, Movimentacao, RecordStatus

TABLE_NAME = os.environ.get("DDB_TABLE", "claud-registros")
TENANT_ID = "default"
DEFAULT_TEXT = "Nao informado"
ACTIVE_STATUS: RecordStatus = "ACTIVE"
DELETED_STATUS: RecordStatus = "DELETED"

_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(TABLE_NAME)


class DuplicateImovelError(Exception):
    pass


def _to_decimal(value: float | int) -> Decimal:
    return Decimal(str(value))


def _to_item(d: Movimentacao) -> dict:
    yyyy_mm = f"{d.ano:04d}-{d.mes:02d}"
    data_evento = d.data_evento.isoformat()
    gsi2sk = _status_sort_key(data_evento, d.id)
    item = {
        "PK": f"TENANT#{TENANT_ID}",
        "SK": f"MOV#{data_evento}#{d.id}",
        "entityType": "MOVIMENTACAO",
        "GSI1PK": f"ANO_MES#{yyyy_mm}",
        "GSI1SK": data_evento,
        "GSI2PK": _status_partition_key(d.status),
        "GSI2SK": gsi2sk,
        "id": d.id,
        "status": d.status,
        "idImovel": d.id_imovel,
        "cidade": d.cidade,
        "edificio": d.edificio,
        "numeroApto": d.numero_apto,
        "areaPrivativa": _to_decimal(d.area_privativa),
        "tipologia": d.tipologia,
        "uso": d.uso,
        "statusEvento": d.status_evento,
        "dataEvento": data_evento,
        "mes": d.mes,
        "ano": d.ano,
        "criadoPor": d.criado_por,
        "criadoEm": d.criado_em,
    }
    if d.data_inicio_contrato:
        item["dataInicioContrato"] = d.data_inicio_contrato.isoformat()
    if d.valor_aluguel is not None:
        item["valorAluguel"] = _to_decimal(d.valor_aluguel)
    if d.dias_vacancia is not None:
        item["diasVacancia"] = d.dias_vacancia
    if d.motivo_desocupacao:
        item["motivoDesocupacao"] = d.motivo_desocupacao
    return item


def _to_imovel_item(imovel: Imovel) -> dict:
    return {
        "PK": f"TENANT#{TENANT_ID}",
        "SK": f"IMOVEL#{imovel.id_imovel}",
        "entityType": "IMOVEL",
        "idImovel": imovel.id_imovel,
        "cidade": imovel.cidade,
        "edificio": imovel.edificio,
        "numeroApto": imovel.numero_apto,
        "areaPrivativa": _to_decimal(imovel.area_privativa),
        "tipologia": imovel.tipologia,
        "uso": imovel.uso,
        "mobiliado": imovel.mobiliado,
        "criadoPor": imovel.criado_por,
        "criadoEm": imovel.criado_em,
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


def _record_status(value: Any) -> RecordStatus:
    return DELETED_STATUS if value == DELETED_STATUS else ACTIVE_STATUS


def _status_partition_key(status: RecordStatus) -> str:
    return f"STATUS#{status}"


def _status_sort_key(data_evento: str, record_id: str) -> str:
    return f"{data_evento}#{record_id}"


def _item_key(record_id: str, data_evento: date) -> dict[str, str]:
    return {
        "PK": f"TENANT#{TENANT_ID}",
        "SK": f"MOV#{data_evento.isoformat()}#{record_id}",
    }


def _imovel_key(id_imovel: str) -> dict[str, str]:
    return {
        "PK": f"TENANT#{TENANT_ID}",
        "SK": f"IMOVEL#{id_imovel}",
    }


def _optional_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return _float(value)


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return _int(value)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _from_item(item: dict) -> Movimentacao:
    data_evento = _date(item.get("dataEvento", item.get("dataFim")))
    data_inicio_contrato = _optional_date(item.get("dataInicioContrato", item.get("dataInicio")))
    mes = _int(item.get("mes"), data_evento.month)
    ano = _int(item.get("ano"), data_evento.year)

    return Movimentacao(
        id=_text(item.get("id"), "sem-id"),
        status=_record_status(item.get("status")),
        id_imovel=_text(item.get("idImovel")),
        cidade=_text(item.get("cidade")),
        edificio=_text(item.get("edificio", item.get("empreendimento"))),
        numero_apto=_text(item.get("numeroApto", item.get("apartamento"))),
        area_privativa=_float(item.get("areaPrivativa")),
        tipologia=_text(item.get("tipologia")),
        uso=_uso(item.get("uso")),
        status_evento=_text(item.get("statusEvento"), "Legado"),
        data_evento=data_evento,
        data_inicio_contrato=data_inicio_contrato,
        valor_aluguel=_optional_float(item.get("valorAluguel")),
        dias_vacancia=_optional_int(item.get("diasVacancia")),
        motivo_desocupacao=_optional_text(item.get("motivoDesocupacao")),
        mes=mes,
        ano=ano,
        criado_por=_text(item.get("criadoPor"), "legacy"),
        criado_em=_text(item.get("criadoEm"), "1970-01-01T00:00:00Z"),
    )


def _from_imovel_item(item: dict) -> Imovel:
    return Imovel(
        id_imovel=_text(item.get("idImovel"), "sem-id"),
        cidade=_text(item.get("cidade")),
        edificio=_text(item.get("edificio")),
        numero_apto=_text(item.get("numeroApto")),
        area_privativa=_float(item.get("areaPrivativa")),
        tipologia=_text(item.get("tipologia"), "Studio"),  # type: ignore[arg-type]
        uso=_uso(item.get("uso")),  # type: ignore[arg-type]
        mobiliado=_text(item.get("mobiliado"), "Não"),  # type: ignore[arg-type]
        criado_por=_text(item.get("criadoPor"), "legacy"),
        criado_em=_text(item.get("criadoEm"), "1970-01-01T00:00:00Z"),
    )


def put(d: Movimentacao) -> None:
    _table.put_item(Item=_to_item(d))


def get(record_id: str, data_evento: date) -> Movimentacao | None:
    resp = _table.get_item(
        Key=_item_key(record_id, data_evento),
        ConsistentRead=True,
    )
    item = resp.get("Item")
    return _from_item(item) if item else None


def imovel_exists_by_id(id_imovel: str) -> bool:
    resp = _table.get_item(
        Key=_imovel_key(id_imovel),
        ConsistentRead=True,
        ProjectionExpression="PK",
    )
    return "Item" in resp


def get_imovel(id_imovel: str) -> Imovel | None:
    resp = _table.get_item(
        Key=_imovel_key(id_imovel),
        ConsistentRead=True,
    )
    item = resp.get("Item")
    return _from_imovel_item(item) if item else None


def put_imovel(imovel: Imovel) -> None:
    try:
        _table.put_item(
            Item=_to_imovel_item(imovel),
            ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            raise DuplicateImovelError from exc
        raise


def list_imoveis(limit: int = 200) -> list[Imovel]:
    items: list[dict] = []
    last = None
    while True:
        kwargs: dict[str, Any] = {
            "KeyConditionExpression": Key("PK").eq(f"TENANT#{TENANT_ID}")
            & Key("SK").begins_with("IMOVEL#"),
        }
        if last:
            kwargs["ExclusiveStartKey"] = last
        resp = _table.query(**kwargs)
        items.extend(resp.get("Items", []))
        last = resp.get("LastEvaluatedKey")
        if not last:
            break

    records = [_from_imovel_item(item) for item in items]
    records.sort(key=lambda item: (item.criado_em, item.id_imovel), reverse=True)
    return records[:limit]


def list_by_month(year: int, month: int) -> list[Movimentacao]:
    yyyy_mm = f"{year:04d}-{month:02d}"
    resp = _table.query(
        IndexName="GSI2",
        KeyConditionExpression=Key("GSI2PK").eq(_status_partition_key(ACTIVE_STATUS))
        & Key("GSI2SK").begins_with(yyyy_mm),
        ScanIndexForward=False,
    )
    return [_from_item(i) for i in resp.get("Items", [])]


def list_all(limit: int = 200) -> list[Movimentacao]:
    resp = _table.query(
        IndexName="GSI2",
        KeyConditionExpression=Key("GSI2PK").eq(_status_partition_key(ACTIVE_STATUS)),
        ScanIndexForward=False,
        Limit=limit,
    )
    return [_from_item(i) for i in resp.get("Items", [])]


def list_all_pages() -> Iterable[Movimentacao]:
    last = None
    while True:
        kwargs = {
            "IndexName": "GSI2",
            "KeyConditionExpression": Key("GSI2PK").eq(_status_partition_key(ACTIVE_STATUS)),
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


def latest_movimentacao_for_imovel(id_imovel: str) -> Movimentacao | None:
    target = id_imovel.strip()
    last = None
    while True:
        kwargs = {
            "IndexName": "GSI2",
            "KeyConditionExpression": Key("GSI2PK").eq(_status_partition_key(ACTIVE_STATUS)),
            "ScanIndexForward": False,
        }
        if last:
            kwargs["ExclusiveStartKey"] = last
        resp = _table.query(**kwargs)
        for item in resp.get("Items", []):
            if _optional_text(item.get("idImovel")) == target:
                return _from_item(item)
        last = resp.get("LastEvaluatedKey")
        if not last:
            break
    return None


def mark_deleted(record_id: str, data_evento: date) -> bool:
    key = _item_key(record_id, data_evento)
    gsi2sk = _status_sort_key(data_evento.isoformat(), record_id)
    try:
        _table.update_item(
            Key=key,
            UpdateExpression="SET #status = :deleted, GSI2PK = :gsi2pk, GSI2SK = :gsi2sk",
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":deleted": DELETED_STATUS,
                ":gsi2pk": _status_partition_key(DELETED_STATUS),
                ":gsi2sk": gsi2sk,
            },
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return False
        raise
    return True
