from datetime import date

from domain.models import Desocupacao, Imovel


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
        id_imovel="FLORIANOPOLIS|PLAZA MEDITERRANEO|326",
        cidade="Florianopolis",
        edificio="Plaza Mediterraneo",
        numero_apto="326",
        area_privativa=72.5,
        tipologia="2Q",
        uso="Residencial",
        mobiliado="Não",
        criado_por="user-1",
        criado_em="2025-05-01T12:00:00Z",
    )


def test_desocupacao_to_item_and_api_dict_format_dates_and_field_names():
    record = _desocupacao()

    assert record.to_item()["data_evento"] == "2025-07-03"
    assert record.to_item()["data_inicio_contrato"] == "2023-10-24"
    assert record.to_api_dict()["idImovel"] == "FLORIANOPOLIS|TOP VISION RESIDENCE|1227"
    assert record.to_api_dict()["numeroApto"] == "1227"
    assert record.to_api_dict()["dataEvento"] == "2025-07-03"
    assert "numero_apto" not in record.to_api_dict()


def test_imovel_to_item_and_api_dict_format_dates_and_field_names():
    record = _imovel()

    assert record.to_item()["id_imovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    assert "data_ultima_locacao" not in record.to_item()
    assert record.to_api_dict()["idImovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    assert "dataUltimaLocacao" not in record.to_api_dict()
    assert "id_imovel" not in record.to_api_dict()
