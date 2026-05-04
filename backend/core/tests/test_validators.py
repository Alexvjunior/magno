import pytest

from domain.validators import ValidationError, validate_desocupacao


def _good_payload(**overrides):
    base = {
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
    base.update(overrides)
    return base


def test_validates_good_payload():
    out = validate_desocupacao(_good_payload())
    assert out.cidade == "Florianopolis"
    assert out.edificio == "Top Vision Residence"
    assert out.numero_apto == "1227"
    assert out.area_privativa == 68.78
    assert out.uso == "Residencial"
    assert out.mes == 7
    assert out.ano == 2025


def test_rejects_missing_required_fields_with_new_names():
    with pytest.raises(ValidationError) as ei:
        validate_desocupacao({})

    errors = ei.value.errors
    assert "cidade" in errors
    assert "edificio" in errors
    assert "numeroApto" in errors
    assert "dataEvento" in errors
    assert "dataInicioContrato" in errors
    assert "empreendimento" not in errors
    assert "apartamento" not in errors


def test_rejects_negative_area():
    with pytest.raises(ValidationError) as ei:
        validate_desocupacao(_good_payload(areaPrivativa=-1))
    assert "areaPrivativa" in ei.value.errors


def test_rejects_invalid_uso():
    with pytest.raises(ValidationError) as ei:
        validate_desocupacao(_good_payload(uso="Industrial"))
    assert "uso" in ei.value.errors


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
