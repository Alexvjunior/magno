import json
import os
from unittest.mock import Mock

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from handlers import create_desocupacao  # noqa: E402


def _event() -> dict:
    return {
        "body": json.dumps(
            {
                "cidade": "Florianopolis",
                "edificio": "Top Vision Residence",
                "numeroApto": "1227",
                "areaPrivativa": 68.78,
                "tipologia": "2 dormitorios",
                "uso": "Residencial",
                "statusEvento": "Desocupado",
                "dataEvento": "2025-07-03",
                "dataInicioContrato": "2023-10-24",
                "valorAluguel": 2500.50,
                "diasVacancia": 12,
                "motivoDesocupacao": "Mudou de estado",
                "mes": 7,
                "ano": 2025,
            }
        ),
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


def test_handler_saves_to_dynamo_then_appends_to_google_sheets(monkeypatch):
    monkeypatch.setattr(create_desocupacao.uuid, "uuid4", lambda: "uuid-123")
    put = Mock()
    append = Mock()
    monkeypatch.setattr(create_desocupacao.dynamo_repo, "put", put)
    monkeypatch.setattr(create_desocupacao.google_sheets_repo, "append_desocupacao", append)

    response = create_desocupacao.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert body["id"] == "uuid-123"
    put.assert_called_once()
    append.assert_called_once()
    assert append.call_args.args[0].id == "uuid-123"


def test_handler_returns_502_when_google_sheets_append_fails_after_dynamo(monkeypatch):
    monkeypatch.setattr(create_desocupacao.uuid, "uuid4", lambda: "uuid-123")
    put = Mock()
    append = Mock(side_effect=RuntimeError("sheets unavailable"))
    monkeypatch.setattr(create_desocupacao.dynamo_repo, "put", put)
    monkeypatch.setattr(create_desocupacao.google_sheets_repo, "append_desocupacao", append)

    response = create_desocupacao.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 502
    assert body["dynamoSaved"] is True
    assert body["id"] == "uuid-123"
    assert body["error"] == "sheets unavailable"
    put.assert_called_once()
    append.assert_called_once()
