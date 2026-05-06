"""Google Sheets integration for desocupacao append operations."""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any

import boto3
from google.oauth2 import service_account
from googleapiclient.discovery import build

from domain.models import Desocupacao, Imovel

LOGGER = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DEFAULT_SPREADSHEET_ID = "1bNzVyloJJmWT9-erNjO-4sR0UNFL0Ct1r9TurN63ekA"
DEFAULT_SHEET_NAME = "MOVIMENTACOES"
DEFAULT_IMOVES_SHEET_NAME = "IMOVEIS"


def desocupacao_to_sheet_row(record: Desocupacao) -> list[Any]:
    return [
        record.cidade,
        record.edificio,
        record.numero_apto,
        record.area_privativa,
        record.tipologia,
        record.uso,
        record.status_evento,
        record.data_evento.strftime("%d/%m/%Y"),
        record.data_inicio_contrato.strftime("%d/%m/%Y"),
        record.valor_aluguel,
        record.dias_vacancia,
        record.motivo_desocupacao,
        record.mes,
        record.ano,
    ]


def imovel_to_sheet_row(record: Imovel) -> list[Any]:
    return [
        record.id_imovel,
        record.cidade,
        record.edificio,
        record.numero_apto,
        record.area_privativa,
        record.tipologia,
        record.uso,
        record.mobiliado,
    ]


def imovel_exists_by_id(id_imovel: str) -> bool:
    spreadsheet_id = _spreadsheet_id()
    sheet_name = _imoveis_sheet_name()
    values = (
        _sheets_service()
        .spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A:A")
        .execute()
        .get("values", [])
    )
    target = id_imovel.strip()
    return any(row and str(row[0]).strip() == target for row in values)


def append_imovel(record: Imovel) -> dict[str, Any]:
    spreadsheet_id = _spreadsheet_id()
    sheet_name = _imoveis_sheet_name()
    range_name = f"{sheet_name}!A:H"
    row = imovel_to_sheet_row(record)

    LOGGER.info("Appending imovel %s to Google Sheets range %s", record.id_imovel, range_name)
    return (
        _sheets_service()
        .spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        )
        .execute()
    )


def append_desocupacao(record: Desocupacao) -> dict[str, Any]:
    spreadsheet_id = _spreadsheet_id()
    sheet_name = _sheet_name()
    row = desocupacao_to_sheet_row(record)

    existing = (
        _sheets_service()
        .spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!B:B")
        .execute()
        .get("values", [])
    )
    target_row = len(existing) + 1
    range_name = f"{sheet_name}!B{target_row}:O{target_row}"

    LOGGER.info("Writing desocupacao %s to Google Sheets range %s", record.id, range_name)
    return (
        _sheets_service()
        .spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": [row]},
        )
        .execute()
    )


def delete_desocupacao_by_imovel_and_date(id_imovel: str, data_evento) -> bool:
    spreadsheet_id = _spreadsheet_id()
    sheet_name = _sheet_name()
    row_number = _find_row_number_by_imovel_and_date(spreadsheet_id, sheet_name, id_imovel, data_evento)
    if row_number is None:
        LOGGER.info("Desocupacao %s %s not found in Google Sheets", id_imovel, data_evento)
        return False

    sheet_id = _sheet_id(spreadsheet_id, sheet_name)
    LOGGER.info("Deleting desocupacao %s from Google Sheets row %s", id_imovel, row_number)
    _sheets_service().spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": row_number - 1,
                            "endIndex": row_number,
                        }
                    }
                }
            ]
        },
    ).execute()
    return True


def delete_desocupacao_by_id(record_id: str) -> bool:
    row_number = _find_row_number_by_id(_spreadsheet_id(), _sheet_name(), record_id)
    if row_number is None:
        LOGGER.info("Desocupacao %s not found in Google Sheets", record_id)
        return False
    sheet_id = _sheet_id(_spreadsheet_id(), _sheet_name())
    _sheets_service().spreadsheets().batchUpdate(
        spreadsheetId=_spreadsheet_id(),
        body={
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": row_number - 1,
                            "endIndex": row_number,
                        }
                    }
                }
            ]
        },
    ).execute()
    return True


def _find_row_number_by_imovel_and_date(
    spreadsheet_id: str,
    sheet_name: str,
    id_imovel: str,
    data_evento,
) -> int | None:
    values = (
        _sheets_service()
        .spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A:I")
        .execute()
        .get("values", [])
    )
    target_id = id_imovel.strip()
    target_date = data_evento.strftime("%d/%m/%Y")
    for index, row in enumerate(values, start=1):
        if index == 1:
            continue
        row_id = str(row[0]).strip() if len(row) >= 1 else ""
        row_date = str(row[8]).strip() if len(row) >= 9 else ""
        if row_id == target_id and row_date == target_date:
            return index
    return None


def _find_row_number_by_id(spreadsheet_id: str, sheet_name: str, record_id: str) -> int | None:
    values = (
        _sheets_service()
        .spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A:A")
        .execute()
        .get("values", [])
    )
    for index, row in enumerate(values, start=1):
        if row and str(row[0]).strip() == record_id:
            return index
    return None


def _sheet_id(spreadsheet_id: str, sheet_name: str) -> int:
    spreadsheet = _sheets_service().spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in spreadsheet.get("sheets", []):
        properties = sheet.get("properties", {})
        if properties.get("title") == sheet_name:
            return int(properties["sheetId"])
    raise RuntimeError(f"Google Sheets tab not found: {sheet_name}")


def _spreadsheet_id() -> str:
    return os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID).strip()


def _sheet_name() -> str:
    return os.environ.get("GOOGLE_SHEETS_SHEET_NAME", DEFAULT_SHEET_NAME).strip()


def _imoveis_sheet_name() -> str:
    return os.environ.get("GOOGLE_SHEETS_IMOVES_SHEET_NAME", DEFAULT_IMOVES_SHEET_NAME).strip()


@lru_cache(maxsize=1)
def _sheets_service():
    credentials = service_account.Credentials.from_service_account_info(
        _service_account_info(),
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


@lru_cache(maxsize=1)
def _service_account_info() -> dict[str, Any]:
    secret_arn = os.environ.get("GOOGLE_SERVICE_ACCOUNT_SECRET_ARN", "").strip()
    if not secret_arn:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_SECRET_ARN env var not set")

    resp = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
    secret_string = resp.get("SecretString")
    if not secret_string:
        raise RuntimeError("Google service account secret must contain SecretString JSON")

    try:
        return json.loads(secret_string)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Google service account secret is not valid JSON") from exc
