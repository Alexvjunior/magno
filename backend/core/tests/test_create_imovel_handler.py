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


def test_handler_returns_409_when_imovel_already_exists_in_dynamo(monkeypatch):
    put = Mock()
    monkeypatch.setattr(create_imovel.dynamo_repo, "imovel_exists_by_id", lambda *_: True)
    monkeypatch.setattr(create_imovel.dynamo_repo, "put_imovel", put)

    response = create_imovel.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 409
    assert body["idImovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    put.assert_not_called()


def test_handler_saves_to_dynamo_only(monkeypatch):
    calls = []

    def dynamo_exists(_id_imovel):
        calls.append("dynamo_exists")
        return False

    def put(record):
        calls.append("put")
        assert record.id_imovel == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
        assert record.status == "ACTIVE"

    monkeypatch.setattr(create_imovel.dynamo_repo, "imovel_exists_by_id", dynamo_exists)
    monkeypatch.setattr(create_imovel.dynamo_repo, "put_imovel", put)

    response = create_imovel.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert body["idImovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    assert body["cidade"] == "Florianopolis"
    assert body["edificio"] == "Plaza Mediterraneo"
    assert body["status"] == "ACTIVE"
    assert body["criadoPor"] == "user-1"
    assert calls == ["dynamo_exists", "put"]


def test_handler_returns_409_when_dynamo_detects_duplicate(monkeypatch):
    put = Mock(side_effect=create_imovel.dynamo_repo.DuplicateImovelError())
    monkeypatch.setattr(create_imovel.dynamo_repo, "imovel_exists_by_id", lambda *_: False)
    monkeypatch.setattr(create_imovel.dynamo_repo, "put_imovel", put)

    response = create_imovel.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 409
    assert body["idImovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
