from datetime import date
from unittest.mock import Mock

from domain.models import Desocupacao
from infra import google_sheets_repo
from infra.google_sheets_repo import desocupacao_to_sheet_row


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
