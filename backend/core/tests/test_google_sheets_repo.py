from datetime import date
from unittest.mock import Mock

from domain.models import Desocupacao, Imovel
from infra import google_sheets_repo
from infra.google_sheets_repo import desocupacao_to_sheet_row, imovel_to_sheet_row


def _record() -> Desocupacao:
    return Desocupacao(
        id="uuid-123",
        status="ACTIVE",
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


def _imovel_record() -> Imovel:
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


def test_desocupacao_to_sheet_row_matches_movimentacoes_order():
    assert desocupacao_to_sheet_row(_record()) == [
        "uuid-123",
        "Florianopolis",
        "Top Vision Residence",
        "1227",
        68.78,
        "2 dormitorios",
        "Residencial",
        "Desocupado",
        "03/07/2025",
        "24/10/2023",
        2500.50,
        12,
        "Mudou de estado",
        7,
        2025,
    ]


def test_delete_desocupacao_by_id_deletes_matching_sheet_row(monkeypatch):
    service = Mock()
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.values.return_value.get.return_value.execute.return_value = {
        "values": [
            ["ID_Imovel"],
            ["other-id"],
            ["uuid-123"],
        ]
    }
    spreadsheets.get.return_value.execute.return_value = {
        "sheets": [{"properties": {"title": "MOVIMENTACOES", "sheetId": 982801841}}]
    }
    spreadsheets.batchUpdate.return_value.execute.return_value = {}

    monkeypatch.setattr(google_sheets_repo, "_spreadsheet_id", lambda: "spreadsheet-1")
    monkeypatch.setattr(google_sheets_repo, "_sheet_name", lambda: "MOVIMENTACOES")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    assert google_sheets_repo.delete_desocupacao_by_id("uuid-123") is True

    spreadsheets.batchUpdate.assert_called_once_with(
        spreadsheetId="spreadsheet-1",
        body={
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": 982801841,
                            "dimension": "ROWS",
                            "startIndex": 2,
                            "endIndex": 3,
                        }
                    }
                }
            ]
        },
    )


def test_delete_desocupacao_by_id_returns_false_when_row_is_missing(monkeypatch):
    service = Mock()
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.values.return_value.get.return_value.execute.return_value = {
        "values": [["ID_Imovel"], ["other-id"]]
    }

    monkeypatch.setattr(google_sheets_repo, "_spreadsheet_id", lambda: "spreadsheet-1")
    monkeypatch.setattr(google_sheets_repo, "_sheet_name", lambda: "MOVIMENTACOES")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    assert google_sheets_repo.delete_desocupacao_by_id("uuid-123") is False
    spreadsheets.batchUpdate.assert_not_called()


def test_imovel_to_sheet_row_matches_imoves_order():
    assert imovel_to_sheet_row(_imovel_record()) == [
        "FLORIANOPOLIS|PLAZA MEDITERRANEO|326",
        "Florianopolis",
        "Plaza Mediterraneo",
        "326",
        72.5,
        "2Q",
        "Residencial",
        "Não",
        "Vago",
        4300.0,
        "10/02/2025",
        "01/05/2025",
        12,
    ]


def test_imovel_exists_by_id_reads_imoves_column_a(monkeypatch):
    service = Mock()
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.values.return_value.get.return_value.execute.return_value = {
        "values": [
            ["ID_Imovel"],
            ["OTHER|BUILDING|101"],
            ["FLORIANOPOLIS|PLAZA MEDITERRANEO|326"],
        ]
    }

    monkeypatch.setattr(google_sheets_repo, "_spreadsheet_id", lambda: "spreadsheet-1")
    monkeypatch.setattr(google_sheets_repo, "_imoveis_sheet_name", lambda: "IMOVES")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    assert google_sheets_repo.imovel_exists_by_id("FLORIANOPOLIS|PLAZA MEDITERRANEO|326") is True
    spreadsheets.values.return_value.get.assert_called_once_with(
        spreadsheetId="spreadsheet-1",
        range="IMOVES!A:A",
    )


def test_append_imovel_appends_to_imoves(monkeypatch):
    service = Mock()
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.values.return_value.append.return_value.execute.return_value = {"updates": {}}

    monkeypatch.setattr(google_sheets_repo, "_spreadsheet_id", lambda: "spreadsheet-1")
    monkeypatch.setattr(google_sheets_repo, "_imoveis_sheet_name", lambda: "IMOVES")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    google_sheets_repo.append_imovel(_imovel_record())

    spreadsheets.values.return_value.append.assert_called_once_with(
        spreadsheetId="spreadsheet-1",
        range="IMOVES!A:M",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [imovel_to_sheet_row(_imovel_record())]},
    )
