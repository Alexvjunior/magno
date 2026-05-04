import os
from datetime import date
from decimal import Decimal

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from domain.models import Desocupacao  # noqa: E402
from infra import dynamo_repo  # noqa: E402


def test_from_item_maps_legacy_fields_to_current_contract():
    item = {
        "id": "legacy-1",
        "empreendimento": "Top Vision Residence",
        "apartamento": "1227",
        "areaPrivativa": Decimal("68.78"),
        "quartos": 2,
        "indice": "IGPM",
        "dataInicio": "2023-10-24",
        "dataFim": "2025-07-03",
        "tempoMeses": Decimal("20.32"),
        "motivoDesocupacao": "Mudou de estado",
        "criadoPor": "user-1",
        "criadoEm": "2025-07-03T12:00:00Z",
    }

    out = dynamo_repo._from_item(item)

    assert out.edificio == "Top Vision Residence"
    assert out.numero_apto == "1227"
    assert out.data_evento.isoformat() == "2025-07-03"
    assert out.data_inicio_contrato.isoformat() == "2023-10-24"
    assert out.mes == 7
    assert out.ano == 2025
    assert out.cidade == "Nao informado"
    assert out.status_evento == "Legado"
    assert out.valor_aluguel == 0.0
    assert out.to_api_dict()["edificio"] == "Top Vision Residence"


def test_to_item_uses_current_contract_and_month_index():
    item = dynamo_repo._to_item(
        Desocupacao(
            id="abc",
            cidade="Florianopolis",
            edificio="Top Vision Residence",
            numero_apto="1227",
            area_privativa=68.78,
            tipologia="2 dormitorios",
            uso="Residencial",
            status_evento="Desocupado",
            data_evento=date(2025, 7, 3),
            data_inicio_contrato=date(2023, 10, 24),
            valor_aluguel=2500.50,
            dias_vacancia=12,
            motivo_desocupacao="Mudou de estado",
            mes=7,
            ano=2025,
            criado_por="user-1",
            criado_em="2025-07-03T12:00:00Z",
        )
    )

    assert item["GSI1PK"] == "ANO_MES#2025-07"
    assert item["GSI1SK"] == "2025-07-03"
    assert item["edificio"] == "Top Vision Residence"
    assert "empreendimento" not in item
