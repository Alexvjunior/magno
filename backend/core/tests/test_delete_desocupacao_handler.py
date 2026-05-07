import json
import os
from datetime import date

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from domain.models import Desocupacao  # noqa: E402
from handlers import delete_movimentacao  # noqa: E402


def _record() -> Desocupacao:
    return Desocupacao(
        id="uuid-123",
        status="ACTIVE",
        id_imovel="FLORIANOPOLIS|TOP VISION RESIDENCE|1227",
        cidade="Florianopolis",
        edificio="Top Vision Residence",
        numero_apto="1227",
        area_privativa=68.78,
        tipologia="2Q",
        uso="Residencial",
        status_evento="Desocupacao",
        data_evento=date(2025, 7, 3),
        data_inicio_contrato=date(2023, 10, 24),
        valor_aluguel=2500.5,
        dias_vacancia=12,
        motivo_desocupacao="Mudança geográfica",
        mes=7,
        ano=2025,
        criado_por="user-1",
        criado_em="2025-07-03T12:00:00Z",
    )


def _event(record_id: str = "uuid-123", data_evento: str = "2025-07-03") -> dict:
    return {
        "pathParameters": {"id": record_id},
        "queryStringParameters": {"dataEvento": data_evento},
    }


def test_handler_marks_record_as_deleted(monkeypatch):
    calls = []

    def mark_deleted(record_id, data_evento):
        calls.append((record_id, data_evento.isoformat()))
        return True

    monkeypatch.setattr(delete_movimentacao.dynamo_repo, "get", lambda *_: _record())
    monkeypatch.setattr(delete_movimentacao.dynamo_repo, "mark_deleted", mark_deleted)
    monkeypatch.setattr(
        delete_movimentacao.google_sheets_repo,
        "delete_movimentacao_by_imovel_and_date",
        lambda id_imovel, data_evento: id_imovel == "FLORIANOPOLIS|TOP VISION RESIDENCE|1227",
    )

    response = delete_movimentacao.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body == {"id": "uuid-123", "status": "DELETED", "sheetsDeleted": True}
    assert calls == [("uuid-123", "2025-07-03")]


def test_handler_returns_400_for_invalid_date(monkeypatch):
    monkeypatch.setattr(delete_movimentacao.dynamo_repo, "get", lambda *_: _record())
    monkeypatch.setattr(delete_movimentacao.dynamo_repo, "mark_deleted", lambda *_: True)
    monkeypatch.setattr(
        delete_movimentacao.google_sheets_repo,
        "delete_movimentacao_by_imovel_and_date",
        lambda *_: True,
    )

    response = delete_movimentacao.handler(_event(data_evento="03/07/2025"), None)

    assert response["statusCode"] == 400


def test_handler_returns_404_when_record_does_not_exist(monkeypatch):
    monkeypatch.setattr(delete_movimentacao.dynamo_repo, "get", lambda *_: None)
    monkeypatch.setattr(delete_movimentacao.dynamo_repo, "mark_deleted", lambda *_: False)
    monkeypatch.setattr(
        delete_movimentacao.google_sheets_repo,
        "delete_movimentacao_by_imovel_and_date",
        lambda *_: True,
    )

    response = delete_movimentacao.handler(_event(), None)

    assert response["statusCode"] == 404


def test_handler_returns_502_when_google_sheets_delete_fails_after_dynamo(monkeypatch):
    monkeypatch.setattr(delete_movimentacao.dynamo_repo, "get", lambda *_: _record())
    monkeypatch.setattr(delete_movimentacao.dynamo_repo, "mark_deleted", lambda *_: True)
    monkeypatch.setattr(
        delete_movimentacao.google_sheets_repo,
        "delete_movimentacao_by_imovel_and_date",
        lambda *_: (_ for _ in ()).throw(RuntimeError("sheets unavailable")),
    )

    response = delete_movimentacao.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 502
    assert body["dynamoDeleted"] is True
    assert body["id"] == "uuid-123"
    assert body["error"] == "sheets unavailable"
