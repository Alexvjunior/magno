import pytest

from domain.validators import ValidationError, validate_desocupacao, validate_imovel


def _good_payload(**overrides):
    base = {
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
        "valorAluguel": 2500.50,
        "diasVacancia": 12,
        "motivoDesocupacao": "Mudou de estado",
        "mes": 7,
        "ano": 2025,
    }
    base.update(overrides)
    return base


def _good_imovel_payload(**overrides):
    base = {
        "cidade": "balne\u00e1rio cambori\u00fa",
        "edificio": "plaza mediterr\u00e2neo",
        "numeroApto": "326",
        "areaPrivativa": 72.5,
        "tipologia": "2Q",
        "uso": "Residencial",
        "mobiliado": "Sim",
    }
    base.update(overrides)
    return base


def test_validates_good_payload():
    out = validate_desocupacao(_good_payload())
    assert out.id_imovel == "FLORIANOPOLIS|TOP VISION RESIDENCE|1227"
    assert out.status_evento == "Desocupacao"
    assert out.mes == 7
    assert out.ano == 2025


def test_rejects_missing_required_fields_with_new_names():
    with pytest.raises(ValidationError) as ei:
        validate_desocupacao({})

    errors = ei.value.errors
    assert "idImovel" in errors
    assert "statusEvento" in errors
    assert "dataEvento" in errors
    assert "dataInicioContrato" in errors
    assert "empreendimento" not in errors
    assert "apartamento" not in errors


def test_rejects_missing_id_imovel():
    with pytest.raises(ValidationError) as ei:
        validate_desocupacao(_good_payload(idImovel=""))
    assert "idImovel" in ei.value.errors


def test_rejects_invalid_status_evento():
    with pytest.raises(ValidationError) as ei:
        validate_desocupacao(_good_payload(statusEvento="Vago"))
    assert "statusEvento" in ei.value.errors


def test_rejects_data_evento_before_data_inicio_contrato():
    with pytest.raises(ValidationError) as ei:
        validate_desocupacao(
            _good_payload(dataInicioContrato="2025-07-10", dataEvento="2025-07-01")
        )
    assert "dataEvento" in ei.value.errors


def test_rejects_non_integer_dias_vacancia():
    with pytest.raises(ValidationError) as ei:
        validate_desocupacao(_good_payload(diasVacancia=1.5))
    assert "diasVacancia" in ei.value.errors


def test_rejects_mes_out_of_range():
    with pytest.raises(ValidationError) as ei:
        validate_desocupacao(_good_payload(mes=13))
    assert "mes" in ei.value.errors


def test_rejects_invalid_ano():
    with pytest.raises(ValidationError) as ei:
        validate_desocupacao(_good_payload(ano=1999))
    assert "ano" in ei.value.errors


def test_validates_imovel_payload_normalizes_text_and_builds_id():
    out = validate_imovel(_good_imovel_payload())

    assert out.id_imovel == "BALNEARIO CAMBORIU|PLAZA MEDITERRANEO|326"
    assert out.cidade == "Balneario Camboriu"
    assert out.edificio == "Plaza Mediterraneo"
    assert out.numero_apto == "326"
    assert out.tipologia == "2Q"
    assert out.mobiliado == "Sim"


def test_rejects_imovel_numero_apto_with_non_digits():
    with pytest.raises(ValidationError) as ei:
        validate_imovel(_good_imovel_payload(numeroApto="326A"))
    assert "numeroApto" in ei.value.errors


def test_rejects_imovel_invalid_enums():
    with pytest.raises(ValidationError) as ei:
        validate_imovel(
            _good_imovel_payload(
                tipologia="5Q",
                uso="Industrial",
                mobiliado="Nao",
            )
        )
    assert "tipologia" in ei.value.errors
    assert "uso" in ei.value.errors
    assert "mobiliado" in ei.value.errors


def test_rejects_imovel_invalid_numbers():
    with pytest.raises(ValidationError) as ei:
        validate_imovel(
            _good_imovel_payload(
                areaPrivativa=0,
            )
        )
    assert "areaPrivativa" in ei.value.errors
