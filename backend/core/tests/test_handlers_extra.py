import json
import os
from datetime import date, datetime, timezone
from unittest.mock import Mock

import pytest

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from domain.models import Desocupacao, Imovel  # noqa: E402
from handlers import (  # noqa: E402
    create_desocupacao,
    create_imovel,
    delete_desocupacao,
    export_xlsx,
    list_desocupacoes,
)


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


def _imovel() -> Imovel:
    return Imovel(
        id_imovel="FLORIANOPOLIS|TOP VISION RESIDENCE|1227",
        cidade="Florianopolis",
        edificio="Top Vision Residence",
        numero_apto="1227",
        area_privativa=68.78,
        tipologia="2Q",
        uso="Residencial",
        mobiliado="NÃ£o",
        criado_por="user-1",
        criado_em="2025-07-03T12:00:00Z",
    )


def _desocupacao_payload(**overrides):
    payload = {
        "cidade": "Florianopolis",
        "edificio": "Top Vision Residence",
        "numeroApto": "1227",
        "areaPrivativa": 68.78,
        "tipologia": "2 dormitorios",
        "uso": "Residencial",
        "idImovel": "FLORIANOPOLIS|TOP VISION RESIDENCE|1227",
        "statusEvento": "Desocupacao",
        "dataEvento": "2025-07-03",
        "dataInicioContrato": "2023-10-24",
        "valorAluguel": 2500.5,
        "diasVacancia": 12,
        "motivoDesocupacao": "Mudou de estado",
        "mes": 7,
        "ano": 2025,
    }
    payload.update(overrides)
    return payload


def _imovel_payload(**overrides):
    payload = {
        "cidade": "Florianopolis",
        "edificio": "Plaza Mediterraneo",
        "numeroApto": "326",
        "areaPrivativa": 72.5,
        "tipologia": "2Q",
        "uso": "Residencial",
        "mobiliado": "Não",
    }
    payload.update(overrides)
    return payload


def test_create_desocupacao_invalid_payload_does_not_persist(monkeypatch):
    put = Mock()
    append = Mock()
    monkeypatch.setattr(create_desocupacao.dynamo_repo, "put", put)
    monkeypatch.setattr(create_desocupacao.google_sheets_repo, "append_desocupacao", append)

    response = create_desocupacao.handler({"body": json.dumps({"cidade": ""})}, None)

    assert response["statusCode"] == 422
    assert "errors" in json.loads(response["body"])
    put.assert_not_called()
    append.assert_not_called()


def test_create_desocupacao_malformed_json_returns_validation_errors(monkeypatch):
    monkeypatch.setattr(create_desocupacao.dynamo_repo, "put", Mock())
    monkeypatch.setattr(create_desocupacao.google_sheets_repo, "append_desocupacao", Mock())

    response = create_desocupacao.handler({"body": "{bad"}, None)

    assert response["statusCode"] == 422
    assert "idImovel" in json.loads(response["body"])["errors"]


def test_create_desocupacao_without_user_claim_uses_anonymous(monkeypatch):
    monkeypatch.setattr(create_desocupacao.uuid, "uuid4", lambda: "uuid-123")
    monkeypatch.setattr(create_desocupacao.dynamo_repo, "get_imovel", lambda *_: _imovel())
    monkeypatch.setattr(create_desocupacao.dynamo_repo, "put", Mock())
    monkeypatch.setattr(create_desocupacao.google_sheets_repo, "append_desocupacao", Mock())

    response = create_desocupacao.handler({"body": json.dumps(_desocupacao_payload())}, None)

    assert response["statusCode"] == 201
    assert json.loads(response["body"])["criadoPor"] == "anonymous"


def test_create_imovel_invalid_payload_does_not_check_or_persist(monkeypatch):
    dynamo_exists = Mock()
    monkeypatch.setattr(create_imovel.dynamo_repo, "imovel_exists_by_id", dynamo_exists)

    response = create_imovel.handler({"body": json.dumps({"cidade": ""})}, None)

    assert response["statusCode"] == 422
    dynamo_exists.assert_not_called()


def test_create_imovel_returns_502_when_dynamo_duplicate_check_fails(monkeypatch):
    monkeypatch.setattr(
        create_imovel.dynamo_repo,
        "imovel_exists_by_id",
        Mock(side_effect=RuntimeError("dynamo down")),
    )

    response = create_imovel.handler({"body": json.dumps(_imovel_payload())}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 502
    assert body["message"] == "Falha ao verificar imovel no DynamoDB"
    assert body["error"] == "dynamo down"


def test_create_imovel_propagates_unexpected_put_error(monkeypatch):
    monkeypatch.setattr(create_imovel.dynamo_repo, "imovel_exists_by_id", lambda *_: False)
    monkeypatch.setattr(
        create_imovel.dynamo_repo,
        "put_imovel",
        Mock(side_effect=RuntimeError("conditional service failure")),
    )

    with pytest.raises(RuntimeError, match="conditional service failure"):
        create_imovel.handler({"body": json.dumps(_imovel_payload())}, None)


def test_list_desocupacoes_without_filters_uses_list_all(monkeypatch):
    list_all = Mock(return_value=[_desocupacao()])
    list_by_month = Mock()
    monkeypatch.setattr(list_desocupacoes.dynamo_repo, "list_all", list_all)
    monkeypatch.setattr(list_desocupacoes.dynamo_repo, "list_by_month", list_by_month)

    response = list_desocupacoes.handler({}, None)

    assert response["statusCode"] == 200
    assert json.loads(response["body"])[0]["id"] == "desoc-1"
    list_all.assert_called_once_with(limit=200)
    list_by_month.assert_not_called()


def test_list_desocupacoes_with_year_and_month_uses_month_index(monkeypatch):
    list_all = Mock()
    list_by_month = Mock(return_value=[_desocupacao()])
    monkeypatch.setattr(list_desocupacoes.dynamo_repo, "list_all", list_all)
    monkeypatch.setattr(list_desocupacoes.dynamo_repo, "list_by_month", list_by_month)

    response = list_desocupacoes.handler(
        {"queryStringParameters": {"ano": "2025", "mes": "7"}},
        None,
    )

    assert response["statusCode"] == 200
    list_by_month.assert_called_once_with(2025, 7)
    list_all.assert_not_called()


def test_list_desocupacoes_with_invalid_month_filter_returns_400(monkeypatch):
    monkeypatch.setattr(list_desocupacoes.dynamo_repo, "list_all", Mock())

    response = list_desocupacoes.handler(
        {"queryStringParameters": {"ano": "2025", "mes": "x"}},
        None,
    )

    assert response["statusCode"] == 400


def test_list_desocupacoes_with_partial_filter_keeps_current_list_all_behavior(monkeypatch):
    list_all = Mock(return_value=[])
    monkeypatch.setattr(list_desocupacoes.dynamo_repo, "list_all", list_all)

    response = list_desocupacoes.handler({"queryStringParameters": {"ano": "2025"}}, None)

    assert response["statusCode"] == 200
    list_all.assert_called_once_with(limit=200)


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2025, 7, 4, 12, 30, 0, tzinfo=tz or timezone.utc)


def test_export_xlsx_for_month_uploads_and_returns_presigned_url(monkeypatch):
    calls = []
    monkeypatch.setattr(export_xlsx, "datetime", _FixedDatetime)
    monkeypatch.setattr(export_xlsx.dynamo_repo, "list_by_month", Mock(return_value=[_desocupacao()]))
    monkeypatch.setattr(export_xlsx, "build_xlsx", Mock(return_value=b"xlsx-data"))
    monkeypatch.setattr(export_xlsx.s3_client, "upload_xlsx", lambda key, data: calls.append(("upload", key, data)))
    monkeypatch.setattr(export_xlsx.s3_client, "presigned_get", lambda key: calls.append(("url", key)) or "https://signed")

    response = export_xlsx.handler(
        {"queryStringParameters": {"ano": "2025", "mes": "7"}},
        None,
    )
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body == {
        "url": "https://signed",
        "filename": "desocupacoes-2025-07-20250704T123000Z.xlsx",
        "count": 1,
    }
    assert calls == [
        ("upload", "exports/2025-07/20250704T123000Z.xlsx", b"xlsx-data"),
        ("url", "exports/2025-07/20250704T123000Z.xlsx"),
    ]


def test_export_xlsx_without_filters_uses_all_pages(monkeypatch):
    monkeypatch.setattr(export_xlsx, "datetime", _FixedDatetime)
    monkeypatch.setattr(export_xlsx.dynamo_repo, "list_all_pages", Mock(return_value=iter([_desocupacao()])))
    monkeypatch.setattr(export_xlsx, "build_xlsx", Mock(return_value=b"xlsx-data"))
    monkeypatch.setattr(export_xlsx.s3_client, "upload_xlsx", Mock())
    monkeypatch.setattr(export_xlsx.s3_client, "presigned_get", Mock(return_value="https://signed"))

    response = export_xlsx.handler({}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["filename"] == "desocupacoes-all-20250704T123000Z.xlsx"
    export_xlsx.dynamo_repo.list_all_pages.assert_called_once()


def test_export_xlsx_invalid_filters_return_400(monkeypatch):
    monkeypatch.setattr(export_xlsx.dynamo_repo, "list_by_month", Mock())

    response = export_xlsx.handler(
        {"queryStringParameters": {"ano": "2025", "mes": "x"}},
        None,
    )

    assert response["statusCode"] == 400
    export_xlsx.dynamo_repo.list_by_month.assert_not_called()


def test_delete_desocupacao_requires_id_and_date(monkeypatch):
    mark_deleted = Mock()
    monkeypatch.setattr(delete_desocupacao.dynamo_repo, "mark_deleted", mark_deleted)

    missing_id = delete_desocupacao.handler(
        {"pathParameters": {"id": " "}, "queryStringParameters": {"dataEvento": "2025-07-03"}},
        None,
    )
    missing_date = delete_desocupacao.handler(
        {"pathParameters": {"id": "abc"}, "queryStringParameters": {}},
        None,
    )

    assert missing_id["statusCode"] == 400
    assert missing_date["statusCode"] == 400
    mark_deleted.assert_not_called()


def test_delete_desocupacao_returns_success_when_sheet_row_was_already_missing(monkeypatch):
    monkeypatch.setattr(delete_desocupacao.dynamo_repo, "get", lambda *_: _desocupacao())
    monkeypatch.setattr(delete_desocupacao.dynamo_repo, "mark_deleted", lambda *_: True)
    monkeypatch.setattr(
        delete_desocupacao.google_sheets_repo,
        "delete_desocupacao_by_imovel_and_date",
        lambda *_: False,
    )

    response = delete_desocupacao.handler(
        {"pathParameters": {"id": "abc"}, "queryStringParameters": {"dataEvento": "2025-07-03"}},
        None,
    )
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["sheetsDeleted"] is False
