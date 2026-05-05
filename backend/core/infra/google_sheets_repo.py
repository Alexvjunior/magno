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

from domain.models import Desocupacao

LOGGER = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DEFAULT_SPREADSHEET_ID = "1bNzVyloJJmWT9-erNjO-4sR0UNFL0Ct1r9TurN63ekA"
DEFAULT_SHEET_NAME = "MOVIMENTACOES"


def desocupacao_to_sheet_row(record: Desocupacao) -> list[Any]:
    return [
        record.id,
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


def append_desocupacao(record: Desocupacao) -> dict[str, Any]:
    spreadsheet_id = _spreadsheet_id()
    sheet_name = _sheet_name()
    range_name = f"{sheet_name}!A:O"
    row = desocupacao_to_sheet_row(record)

    LOGGER.info("Appending desocupacao %s to Google Sheets range %s", record.id, range_name)
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


def _spreadsheet_id() -> str:
    return os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID).strip()


def _sheet_name() -> str:
    return os.environ.get("GOOGLE_SHEETS_SHEET_NAME", DEFAULT_SHEET_NAME).strip()


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
