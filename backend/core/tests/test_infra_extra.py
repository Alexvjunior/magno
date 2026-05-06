import os
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from domain.models import Desocupacao  # noqa: E402
from infra import dynamo_repo, google_sheets_repo, s3_client  # noqa: E402


def _desocupacao() -> Desocupacao:
    return Desocupacao(
        id="desoc-1",
        status="ACTIVE",
        id_imovel="FLORIANOPOLIS|TOP VISION RESIDENCE|1227",
        cidade="Florianopolis",
        edificio="Top Vision Residence",
        numero_apto="1227",
        area_privativa=68.78,
        tipologia="2 dormitorios",
        uso="Residencial",
        status_evento="Desocupacao",
        data_evento=date(2025, 7, 3),
        data_inicio_contrato=date(2023, 10, 24),
        valor_aluguel=2500.5,
        dias_vacancia=12,
        motivo_desocupacao="Mudou de estado",
        mes=7,
        ano=2025,
        criado_por="user-1",
        criado_em="2025-07-03T12:00:00Z",
    )


def test_dynamo_put_writes_serialized_item(monkeypatch):
    table = Mock()
    monkeypatch.setattr(dynamo_repo, "_table", table)

    dynamo_repo.put(_desocupacao())

    table.put_item.assert_called_once()
    item = table.put_item.call_args.kwargs["Item"]
    assert item["SK"] == "DESOC#2025-07-03#desoc-1"
    assert item["areaPrivativa"] == Decimal("68.78")


def test_dynamo_list_by_month_queries_active_status_prefix(monkeypatch):
    table = Mock()
    table.query.return_value = {"Items": [dynamo_repo._to_item(_desocupacao())]}
    monkeypatch.setattr(dynamo_repo, "_table", table)

    out = dynamo_repo.list_by_month(2025, 7)

    assert [item.id for item in out] == ["desoc-1"]
    kwargs = table.query.call_args.kwargs
    assert kwargs["IndexName"] == "GSI2"
    assert kwargs["ScanIndexForward"] is False


def test_dynamo_list_all_queries_active_records_with_limit(monkeypatch):
    table = Mock()
    table.query.return_value = {"Items": [dynamo_repo._to_item(_desocupacao())]}
    monkeypatch.setattr(dynamo_repo, "_table", table)

    out = dynamo_repo.list_all(limit=5)

    assert [item.id for item in out] == ["desoc-1"]
    assert table.query.call_args.kwargs["Limit"] == 5


def test_dynamo_list_all_pages_yields_paginated_records(monkeypatch):
    table = Mock()
    table.query.side_effect = [
        {
            "Items": [dynamo_repo._to_item(_desocupacao())],
            "LastEvaluatedKey": {"PK": "TENANT#default", "SK": "DESOC#1"},
        },
        {"Items": [dynamo_repo._to_item(_desocupacao())]},
    ]
    monkeypatch.setattr(dynamo_repo, "_table", table)

    out = list(dynamo_repo.list_all_pages())

    assert [item.id for item in out] == ["desoc-1", "desoc-1"]
    assert table.query.call_args_list[1].kwargs["ExclusiveStartKey"] == {
        "PK": "TENANT#default",
        "SK": "DESOC#1",
    }


def test_dynamo_from_item_defaults_invalid_legacy_values():
    out = dynamo_repo._from_item(
        {
            "id": "",
            "status": "ARCHIVED",
            "dataEvento": "not-a-date",
            "dataInicioContrato": "not-a-date",
            "areaPrivativa": "bad",
            "valorAluguel": "bad",
            "diasVacancia": "bad",
            "uso": "Industrial",
        }
    )

    assert out.id == "sem-id"
    assert out.status == "ACTIVE"
    assert out.data_evento.isoformat() == "1970-01-01"
    assert out.area_privativa == 0.0
    assert out.valor_aluguel == 0.0
    assert out.dias_vacancia == 0
    assert out.uso == "Residencial"


def test_dynamo_mark_deleted_propagates_non_conditional_client_error(monkeypatch):
    error = ClientError({"Error": {"Code": "ProvisionedThroughputExceededException"}}, "UpdateItem")
    table = Mock()
    table.update_item.side_effect = error
    monkeypatch.setattr(dynamo_repo, "_table", table)

    with pytest.raises(ClientError):
        dynamo_repo.mark_deleted("abc", date(2025, 7, 3))


def test_google_sheets_append_desocupacao_appends_to_movimentacoes(monkeypatch):
    service = Mock()
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.values.return_value.get.return_value.execute.return_value = {
        "values": [["header"], ["existing"]]
    }
    spreadsheets.values.return_value.update.return_value.execute.return_value = {"updates": {}}
    monkeypatch.setattr(google_sheets_repo, "_spreadsheet_id", lambda: "spreadsheet-1")
    monkeypatch.setattr(google_sheets_repo, "_sheet_name", lambda: "MOVIMENTACOES")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    google_sheets_repo.append_desocupacao(_desocupacao())

    spreadsheets.values.return_value.update.assert_called_once()
    assert spreadsheets.values.return_value.update.call_args.kwargs["range"] == "MOVIMENTACOES!B3:O3"


def test_google_sheets_sheet_id_raises_when_tab_is_missing(monkeypatch):
    service = Mock()
    service.spreadsheets.return_value.get.return_value.execute.return_value = {
        "sheets": [{"properties": {"title": "OTHER", "sheetId": 1}}],
    }
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    with pytest.raises(RuntimeError, match="Google Sheets tab not found"):
        google_sheets_repo._sheet_id("spreadsheet-1", "MOVIMENTACOES")


def test_google_sheets_env_helpers_trim_values(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEETS_SPREADSHEET_ID", " sheet-1 ")
    monkeypatch.setenv("GOOGLE_SHEETS_SHEET_NAME", " MOVIMENTACOES ")
    monkeypatch.setenv("GOOGLE_SHEETS_IMOVES_SHEET_NAME", " IMOVEIS ")

    assert google_sheets_repo._spreadsheet_id() == "sheet-1"
    assert google_sheets_repo._sheet_name() == "MOVIMENTACOES"
    assert google_sheets_repo._imoveis_sheet_name() == "IMOVEIS"


def test_google_sheets_service_account_secret_validation(monkeypatch):
    google_sheets_repo._service_account_info.cache_clear()
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_SECRET_ARN", raising=False)
    with pytest.raises(RuntimeError, match="env var not set"):
        google_sheets_repo._service_account_info()

    google_sheets_repo._service_account_info.cache_clear()
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_SECRET_ARN", "arn-1")
    monkeypatch.setattr(
        google_sheets_repo.boto3,
        "client",
        lambda *_: Mock(get_secret_value=Mock(return_value={})),
    )
    with pytest.raises(RuntimeError, match="SecretString JSON"):
        google_sheets_repo._service_account_info()

    google_sheets_repo._service_account_info.cache_clear()
    monkeypatch.setattr(
        google_sheets_repo.boto3,
        "client",
        lambda *_: Mock(get_secret_value=Mock(return_value={"SecretString": "{bad"})),
    )
    with pytest.raises(RuntimeError, match="not valid JSON"):
        google_sheets_repo._service_account_info()

    google_sheets_repo._service_account_info.cache_clear()


def test_s3_upload_xlsx_requires_bucket_and_sets_content_type(monkeypatch):
    monkeypatch.setattr(s3_client, "BUCKET", "")
    with pytest.raises(RuntimeError, match="EXPORTS_BUCKET"):
        s3_client.upload_xlsx("exports/a.xlsx", b"data")

    s3 = Mock()
    monkeypatch.setattr(s3_client, "BUCKET", "bucket-1")
    monkeypatch.setattr(s3_client, "_s3", s3)
    s3_client.upload_xlsx("exports/a.xlsx", b"data")

    s3.put_object.assert_called_once_with(
        Bucket="bucket-1",
        Key="exports/a.xlsx",
        Body=b"data",
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def test_s3_presigned_get_uses_bucket_key_and_expiration(monkeypatch):
    s3 = Mock()
    s3.generate_presigned_url.return_value = "https://signed"
    monkeypatch.setattr(s3_client, "BUCKET", "bucket-1")
    monkeypatch.setattr(s3_client, "_s3", s3)

    assert s3_client.presigned_get("exports/a.xlsx", expires_seconds=60) == "https://signed"
    s3.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "bucket-1", "Key": "exports/a.xlsx"},
        ExpiresIn=60,
    )
