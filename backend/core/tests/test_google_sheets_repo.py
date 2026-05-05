from datetime import date

from domain.models import Desocupacao
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
