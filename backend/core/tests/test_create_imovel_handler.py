import json
import os
from unittest.mock import Mock

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from handlers import create_imovel  # noqa: E402


def _payload(**overrides) -> dict:
    base = {
        "cidade": "Florianopolis",
        "edificio": "Plaza Mediterraneo",
        "numeroApto": "326",
        "areaPrivativa": 72.5,
        "tipologia": "2Q",
        "uso": "Residencial",
        "mobiliado": "Não",
        "statusAtual": "Vago",
        "valorAluguelAtual": 4300.0,
        "dataUltimaLocacao": "2025-02-10",
        "dataUltimaDesocupacao": "2025-05-01",
        "diasVacanciaAtual": 12,
    }
    base.update(overrides)
    return base


def _event(**overrides) -> dict:
    return {
        "body": json.dumps(_payload(**overrides)),
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "user-1",
                    }
                }
            }
        },
    }


def test_handler_returns_409_when_imovel_already_exists_in_google_sheets(monkeypatch):
    put = Mock()
    append = Mock()
    monkeypatch.setattr(create_imovel.google_sheets_repo, "imovel_exists_by_id", lambda *_: True)
    monkeypatch.setattr(create_imovel.dynamo_repo, "put_imovel", put)
    monkeypatch.setattr(create_imovel.google_sheets_repo, "append_imovel", append)

    response = create_imovel.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 409
    assert body["idImovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    put.assert_not_called()
    append.assert_not_called()


def test_handler_saves_to_dynamo_then_appends_to_google_sheets(monkeypatch):
    calls = []

    def put(record):
        calls.append("put")
        assert record.id_imovel == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"

    def append(record):
        calls.append("append")
        assert record.id_imovel == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"

    monkeypatch.setattr(create_imovel.google_sheets_repo, "imovel_exists_by_id", lambda *_: False)
    monkeypatch.setattr(create_imovel.dynamo_repo, "put_imovel", put)
    monkeypatch.setattr(create_imovel.google_sheets_repo, "append_imovel", append)

    response = create_imovel.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert body["idImovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    assert body["cidade"] == "Florianopolis"
    assert body["edificio"] == "Plaza Mediterraneo"
    assert body["criadoPor"] == "user-1"
    assert calls == ["put", "append"]


def test_handler_returns_409_when_dynamo_detects_duplicate(monkeypatch):
    append = Mock()
    put = Mock(side_effect=create_imovel.dynamo_repo.DuplicateImovelError())
    monkeypatch.setattr(create_imovel.google_sheets_repo, "imovel_exists_by_id", lambda *_: False)
    monkeypatch.setattr(create_imovel.dynamo_repo, "put_imovel", put)
    monkeypatch.setattr(create_imovel.google_sheets_repo, "append_imovel", append)

    response = create_imovel.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 409
    assert body["idImovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    append.assert_not_called()


def test_handler_returns_502_when_google_sheets_append_fails_after_dynamo(monkeypatch):
    put = Mock()
    append = Mock(side_effect=RuntimeError("sheets unavailable"))
    monkeypatch.setattr(create_imovel.google_sheets_repo, "imovel_exists_by_id", lambda *_: False)
    monkeypatch.setattr(create_imovel.dynamo_repo, "put_imovel", put)
    monkeypatch.setattr(create_imovel.google_sheets_repo, "append_imovel", append)

    response = create_imovel.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 502
    assert body["dynamoSaved"] is True
    assert body["idImovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    assert body["error"] == "sheets unavailable"
    put.assert_called_once()
    append.assert_called_once()
