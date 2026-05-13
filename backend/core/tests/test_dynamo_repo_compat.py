import os
from dataclasses import replace
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from botocore.exceptions import ClientError  # noqa: E402
from domain.models import Desocupacao, Imovel  # noqa: E402
from infra import dynamo_repo  # noqa: E402


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
        "motivoDesocupacao": "Mudança geográfica",
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
    assert out.status == "ACTIVE"
    assert out.id_imovel == "Nao informado"
    assert out.status_evento == "Legado"
    assert out.valor_aluguel is None
    assert out.to_api_dict()["edificio"] == "Top Vision Residence"


def test_to_item_uses_current_contract_and_month_index():
    item = dynamo_repo._to_item(
        Desocupacao(
            id="abc",
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
            valor_aluguel=2500.50,
            dias_vacancia=12,
            motivo_desocupacao="Mudança geográfica",
            mes=7,
            ano=2025,
            criado_por="user-1",
            criado_em="2025-07-03T12:00:00Z",
        )
    )

    assert item["GSI1PK"] == "ANO_MES#2025-07"
    assert item["GSI1SK"] == "2025-07-03"
    assert item["GSI2PK"] == "STATUS#ACTIVE"
    assert item["GSI2SK"] == "2025-07-03#abc"
    assert item["status"] == "ACTIVE"
    assert item["idImovel"] == "FLORIANOPOLIS|TOP VISION RESIDENCE|1227"
    assert item["edificio"] == "Top Vision Residence"
    assert "empreendimento" not in item


def test_mark_deleted_updates_status_index(monkeypatch):
    table = Mock()
    monkeypatch.setattr(dynamo_repo, "_table", table)

    assert dynamo_repo.mark_deleted("abc", date(2025, 7, 3)) is True

    table.update_item.assert_called_once()
    kwargs = table.update_item.call_args.kwargs
    assert kwargs["Key"] == {
        "PK": "TENANT#default",
        "SK": "MOV#2025-07-03#abc",
    }
    assert kwargs["ExpressionAttributeValues"][":deleted"] == "DELETED"
    assert kwargs["ExpressionAttributeValues"][":gsi2pk"] == "STATUS#DELETED"
    assert kwargs["ExpressionAttributeValues"][":gsi2sk"] == "2025-07-03#abc"


def test_mark_deleted_returns_false_for_missing_item(monkeypatch):
    error = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "missing"}},
        "UpdateItem",
    )
    table = Mock()
    table.update_item.side_effect = error
    monkeypatch.setattr(dynamo_repo, "_table", table)

    assert dynamo_repo.mark_deleted("missing", date(2025, 7, 3)) is False


def test_to_imovel_item_uses_imovel_entity_key():
    item = dynamo_repo._to_imovel_item(_imovel())

    assert item["PK"] == "TENANT#default"
    assert item["SK"] == "IMOVEL#FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    assert item["entityType"] == "IMOVEL"
    assert item["idImovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    assert item["status"] == "ACTIVE"
    assert item["cidade"] == "Florianopolis"
    assert item["areaPrivativa"] == Decimal("72.5")
    assert "valorAluguelAtual" not in item
    assert "dataUltimaLocacao" not in item
    assert "dataUltimaDesocupacao" not in item


def test_from_imovel_item_maps_current_contract():
    out = dynamo_repo._from_imovel_item(dynamo_repo._to_imovel_item(_imovel()))

    assert out.id_imovel == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    assert out.cidade == "Florianopolis"
    assert out.edificio == "Plaza Mediterraneo"
    assert out.numero_apto == "326"
    assert out.area_privativa == 72.5
    assert out.tipologia == "2Q"
    assert out.uso == "Residencial"
    assert out.mobiliado == _imovel().mobiliado
    assert out.criado_por == "user-1"
    assert out.status == "ACTIVE"
    assert out.to_api_dict()["idImovel"] == "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"


def test_put_imovel_uses_conditional_put(monkeypatch):
    table = Mock()
    monkeypatch.setattr(dynamo_repo, "_table", table)

    dynamo_repo.put_imovel(_imovel())

    table.put_item.assert_called_once()
    kwargs = table.put_item.call_args.kwargs
    assert kwargs["Item"]["SK"] == "IMOVEL#FLORIANOPOLIS|PLAZA MEDITERRANEO|326"
    assert kwargs["ConditionExpression"] == "attribute_not_exists(PK) AND attribute_not_exists(SK)"


def test_imovel_exists_by_id_uses_imovel_key_with_consistent_read(monkeypatch):
    table = Mock()
    table.get_item.return_value = {"Item": {"PK": "TENANT#default"}}
    monkeypatch.setattr(dynamo_repo, "_table", table)

    assert dynamo_repo.imovel_exists_by_id("FLORIANOPOLIS|PLAZA MEDITERRANEO|326") is True

    table.get_item.assert_called_once_with(
        Key={
            "PK": "TENANT#default",
            "SK": "IMOVEL#FLORIANOPOLIS|PLAZA MEDITERRANEO|326",
        },
        ConsistentRead=True,
        ProjectionExpression="PK",
    )


def test_imovel_exists_by_id_returns_false_when_missing(monkeypatch):
    table = Mock()
    table.get_item.return_value = {}
    monkeypatch.setattr(dynamo_repo, "_table", table)

    assert dynamo_repo.imovel_exists_by_id("FLORIANOPOLIS|PLAZA MEDITERRANEO|326") is False


def test_get_desocupacao_returns_record_by_key(monkeypatch):
    table = Mock()
    record = dynamo_repo._from_item(
        dynamo_repo._to_item(
            Desocupacao(
                id="abc",
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
        )
    )
    table.get_item.return_value = {"Item": dynamo_repo._to_item(record)}
    monkeypatch.setattr(dynamo_repo, "_table", table)

    assert dynamo_repo.get("abc", date(2025, 7, 3)).id_imovel == "FLORIANOPOLIS|TOP VISION RESIDENCE|1227"
    table.get_item.assert_called_once_with(
        Key={"PK": "TENANT#default", "SK": "MOV#2025-07-03#abc"},
        ConsistentRead=True,
    )


def test_get_imovel_returns_none_when_missing(monkeypatch):
    table = Mock()
    table.get_item.return_value = {}
    monkeypatch.setattr(dynamo_repo, "_table", table)

    assert dynamo_repo.get_imovel("missing") is None


def test_from_imovel_item_defaults_legacy_status_to_active():
    item = dynamo_repo._to_imovel_item(_imovel())
    item.pop("status")

    assert dynamo_repo._from_imovel_item(item).status == "ACTIVE"


def test_list_imoveis_queries_prefix_pages_and_sorts_by_criado_em(monkeypatch):
    older = replace(
        _imovel(),
        id_imovel="FLORIANOPOLIS|PLAZA MEDITERRANEO|326",
        criado_em="2025-05-01T12:00:00Z",
    )
    newer = replace(
        _imovel(),
        id_imovel="SAO JOSE|RESIDENCIAL ILHA|1201",
        criado_em="2025-05-03T12:00:00Z",
    )
    deleted = replace(
        _imovel(),
        id_imovel="SAO JOSE|RESIDENCIAL ILHA|1202",
        criado_em="2025-05-04T12:00:00Z",
        status="DELETED",
    )
    table = Mock()
    table.query.side_effect = [
        {
            "Items": [dynamo_repo._to_imovel_item(older)],
            "LastEvaluatedKey": {"PK": "TENANT#default", "SK": "IMOVEL#OLD"},
        },
        {"Items": [dynamo_repo._to_imovel_item(newer), dynamo_repo._to_imovel_item(deleted)]},
    ]
    monkeypatch.setattr(dynamo_repo, "_table", table)

    out = dynamo_repo.list_imoveis(limit=1)

    assert [item.id_imovel for item in out] == ["SAO JOSE|RESIDENCIAL ILHA|1201"]
    assert table.query.call_count == 2
    first_call = table.query.call_args_list[0].kwargs
    second_call = table.query.call_args_list[1].kwargs
    assert "KeyConditionExpression" in first_call
    assert second_call["ExclusiveStartKey"] == {"PK": "TENANT#default", "SK": "IMOVEL#OLD"}


def test_mark_imovel_deleted_updates_status(monkeypatch):
    table = Mock()
    monkeypatch.setattr(dynamo_repo, "_table", table)

    assert dynamo_repo.mark_imovel_deleted("FLORIANOPOLIS|PLAZA MEDITERRANEO|326") is True

    table.update_item.assert_called_once()
    kwargs = table.update_item.call_args.kwargs
    assert kwargs["Key"] == {
        "PK": "TENANT#default",
        "SK": "IMOVEL#FLORIANOPOLIS|PLAZA MEDITERRANEO|326",
    }
    assert kwargs["ExpressionAttributeValues"][":deleted"] == "DELETED"


def test_mark_imovel_deleted_returns_false_for_missing_item(monkeypatch):
    error = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "missing"}},
        "UpdateItem",
    )
    table = Mock()
    table.update_item.side_effect = error
    monkeypatch.setattr(dynamo_repo, "_table", table)

    assert dynamo_repo.mark_imovel_deleted("missing") is False


def test_put_imovel_raises_duplicate_for_conditional_failure(monkeypatch):
    error = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "duplicate"}},
        "PutItem",
    )
    table = Mock()
    table.put_item.side_effect = error
    monkeypatch.setattr(dynamo_repo, "_table", table)

    try:
        dynamo_repo.put_imovel(_imovel())
    except dynamo_repo.DuplicateImovelError:
        pass
    else:
        raise AssertionError("Expected DuplicateImovelError")
