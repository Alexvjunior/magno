import json
import os
from datetime import date

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from domain.models import Imovel
from handlers import list_imoveis


def _record() -> Imovel:
    return Imovel(
        id_imovel="FLORIANOPOLIS|PLAZA MEDITERRANEO|326",
        cidade="Florianopolis",
        edificio="Plaza Mediterraneo",
        numero_apto="326",
        area_privativa=72.5,
        tipologia="2Q",
        uso="Residencial",
        mobiliado="Não",
        status_atual="Vago",
        valor_aluguel_atual=4300.0,
        data_ultima_locacao=date(2025, 2, 10),
        data_ultima_desocupacao=date(2025, 5, 1),
        dias_vacancia_atual=12,
        criado_por="user-1",
        criado_em="2025-05-01T12:00:00Z",
    )


def test_handler_lists_imoveis(monkeypatch):
    monkeypatch.setattr(list_imoveis.dynamo_repo, "list_imoveis", lambda limit=200: [_record()])

    response = list_imoveis.handler({}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body == [_record().to_api_dict()]
