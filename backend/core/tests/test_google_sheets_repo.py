from datetime import date
from unittest.mock import Mock

from domain.models import Desocupacao, Imovel
from infra import google_sheets_repo
from infra.google_sheets_repo import movimentacao_to_sheet_row, imovel_to_sheet_row


def _record() -> Desocupacao:
    return Desocupacao(
        id="uuid-123",
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
        criado_por="user-1",
        criado_em="2025-05-01T12:00:00Z",
    )


def test_movimentacao_to_sheet_row_matches_movimentacoes_order():
    assert movimentacao_to_sheet_row(_record()) == [
        "Florianopolis",
        "Top Vision Residence",
        "1227",
        68.78,
        "2 dormitorios",
        "Residencial",
        "Desocupacao",
        "03/07/2025",
        "24/10/2023",
        2500.50,
        12,
        "Mudança geográfica",
        7,
        2025,
    ]


def _sheet_row(id_imovel: str, status_evento: str, data_evento: str) -> list[str]:
    row = [""] * 15
    row[0] = id_imovel
    row[7] = status_evento
    row[8] = data_evento
    return row


def test_latest_status_evento_by_imovel_returns_latest_matching_sheet_status(monkeypatch):
    service = Mock()
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.values.return_value.get.return_value.execute.return_value = {
        "values": [
            _sheet_row("ID_Imovel", "Status Evento", "Data Evento"),
            _sheet_row("FLORIANOPOLIS|TOP VISION RESIDENCE|1227", "Locacao", "2025-07-01"),
            _sheet_row("OTHER|BUILDING|101", "Locacao", "04/07/2025"),
            _sheet_row("FLORIANOPOLIS|TOP VISION RESIDENCE|1227", "Desocupacao", "03/07/2025"),
        ]
    }
    monkeypatch.setattr(google_sheets_repo, "_spreadsheet_id", lambda: "spreadsheet-1")
    monkeypatch.setattr(google_sheets_repo, "_sheet_name", lambda: "MOVIMENTACOES")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    assert (
        google_sheets_repo.latest_status_evento_by_imovel(
            "FLORIANOPOLIS|TOP VISION RESIDENCE|1227"
        )
        == "Desocupacao"
    )

    spreadsheets.values.return_value.get.assert_called_once_with(
        spreadsheetId="spreadsheet-1",
        range="MOVIMENTACOES!A:O",
    )
    spreadsheets.values.return_value.update.assert_not_called()
    spreadsheets.batchUpdate.assert_not_called()


def test_latest_status_evento_by_imovel_returns_none_when_missing(monkeypatch):
    service = Mock()
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.values.return_value.get.return_value.execute.return_value = {
        "values": [
            _sheet_row("ID_Imovel", "Status Evento", "Data Evento"),
            _sheet_row("OTHER|BUILDING|101", "Locacao", "04/07/2025"),
        ]
    }
    monkeypatch.setattr(google_sheets_repo, "_spreadsheet_id", lambda: "spreadsheet-1")
    monkeypatch.setattr(google_sheets_repo, "_sheet_name", lambda: "MOVIMENTACOES")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    assert google_sheets_repo.latest_status_evento_by_imovel("missing") is None
    spreadsheets.values.return_value.update.assert_not_called()
    spreadsheets.batchUpdate.assert_not_called()


def test_delete_movimentacao_by_imovel_and_date_deletes_matching_sheet_row(monkeypatch):
    service = Mock()
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.values.return_value.get.return_value.execute.return_value = {
        "values": [
            ["ID_Imovel", "", "", "", "", "", "", "", "Data Evento"],
            ["other-id", "", "", "", "", "", "", "", "03/07/2025"],
            ["FLORIANOPOLIS|TOP VISION RESIDENCE|1227", "", "", "", "", "", "", "", "03/07/2025"],
        ]
    }
    spreadsheets.get.return_value.execute.return_value = {
        "sheets": [{"properties": {"title": "MOVIMENTACOES", "sheetId": 982801841}}]
    }
    spreadsheets.batchUpdate.return_value.execute.return_value = {}

    monkeypatch.setattr(google_sheets_repo, "_spreadsheet_id", lambda: "spreadsheet-1")
    monkeypatch.setattr(google_sheets_repo, "_sheet_name", lambda: "MOVIMENTACOES")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    assert (
        google_sheets_repo.delete_movimentacao_by_imovel_and_date(
            "FLORIANOPOLIS|TOP VISION RESIDENCE|1227",
            date(2025, 7, 3),
        )
        is True
    )

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


def test_delete_movimentacao_by_imovel_and_date_returns_false_when_row_is_missing(monkeypatch):
    service = Mock()
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.values.return_value.get.return_value.execute.return_value = {
        "values": [["ID_Imovel", "", "", "", "", "", "", "", "Data Evento"], ["other-id"]]
    }

    monkeypatch.setattr(google_sheets_repo, "_spreadsheet_id", lambda: "spreadsheet-1")
    monkeypatch.setattr(google_sheets_repo, "_sheet_name", lambda: "MOVIMENTACOES")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    assert (
        google_sheets_repo.delete_movimentacao_by_imovel_and_date(
            "FLORIANOPOLIS|TOP VISION RESIDENCE|1227",
            date(2025, 7, 3),
        )
        is False
    )
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
    monkeypatch.setattr(google_sheets_repo, "_imoveis_sheet_name", lambda: "IMOVEIS")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    assert google_sheets_repo.imovel_exists_by_id("FLORIANOPOLIS|PLAZA MEDITERRANEO|326") is True
    spreadsheets.values.return_value.get.assert_called_once_with(
        spreadsheetId="spreadsheet-1",
        range="IMOVEIS!A:A",
    )


def test_append_imovel_appends_to_imoves(monkeypatch):
    service = Mock()
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.values.return_value.append.return_value.execute.return_value = {"updates": {}}

    monkeypatch.setattr(google_sheets_repo, "_spreadsheet_id", lambda: "spreadsheet-1")
    monkeypatch.setattr(google_sheets_repo, "_imoveis_sheet_name", lambda: "IMOVEIS")
    monkeypatch.setattr(google_sheets_repo, "_sheets_service", lambda: service)

    google_sheets_repo.append_imovel(_imovel_record())

    spreadsheets.values.return_value.append.assert_called_once_with(
        spreadsheetId="spreadsheet-1",
        range="IMOVEIS!A:H",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [imovel_to_sheet_row(_imovel_record())]},
    )
