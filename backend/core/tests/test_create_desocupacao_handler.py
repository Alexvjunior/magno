import json
import os
from datetime import date
from unittest.mock import Mock

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from domain.models import Imovel  # noqa: E402
from handlers import create_desocupacao  # noqa: E402


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
        status_atual="Vago",
        valor_aluguel_atual=2500.50,
        data_ultima_locacao=date(2023, 10, 24),
        data_ultima_desocupacao=date(2025, 7, 3),
        dias_vacancia_atual=12,
        criado_por="user-1",
        criado_em="2025-07-03T12:00:00Z",
    )


def _event() -> dict:
    return {
        "body": json.dumps(
            {
                "idImovel": "FLORIANOPOLIS|TOP VISION RESIDENCE|1227",
                "statusEvento": "Desocupacao",
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
    monkeypatch.setattr(create_desocupacao.dynamo_repo, "get_imovel", lambda *_: _imovel())
    monkeypatch.setattr(create_desocupacao.dynamo_repo, "put", put)
    monkeypatch.setattr(create_desocupacao.google_sheets_repo, "append_desocupacao", append)

    response = create_desocupacao.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert body["id"] == "uuid-123"
    assert body["status"] == "ACTIVE"
    put.assert_called_once()
    append.assert_called_once()
    assert append.call_args.args[0].id == "uuid-123"
    assert append.call_args.args[0].id_imovel == "FLORIANOPOLIS|TOP VISION RESIDENCE|1227"
    assert append.call_args.args[0].status == "ACTIVE"


def test_handler_returns_502_when_google_sheets_append_fails_after_dynamo(monkeypatch):
    monkeypatch.setattr(create_desocupacao.uuid, "uuid4", lambda: "uuid-123")
    put = Mock()
    append = Mock(side_effect=RuntimeError("sheets unavailable"))
    monkeypatch.setattr(create_desocupacao.dynamo_repo, "get_imovel", lambda *_: _imovel())
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
