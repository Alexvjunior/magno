"""Validators for the Desocupacao input payload.

Returns a cleaned dataclass or raises ValidationError. The accepted payload
mirrors the React form contract in frontend/src/types.ts.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from .models import DesocupacaoInput

ALLOWED_USOS = {"Residencial", "Comercial"}


class ValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        super().__init__("Validation failed")
        self.errors = errors


def _parse_date(value: Any, field: str, errors: dict[str, str]) -> date | None:
    if not isinstance(value, str) or not value.strip():
        errors[field] = "Obrigatório"
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        errors[field] = "Data inválida (use YYYY-MM-DD)"
        return None


def _str(value: Any, field: str, errors: dict[str, str], min_len: int, max_len: int) -> str | None:
    if not isinstance(value, str):
        errors[field] = "Obrigatório"
        return None
    s = value.strip()
    if len(s) < min_len:
        errors[field] = "Obrigatório" if min_len == 1 else f"Mínimo {min_len} caracteres"
        return None
    if len(s) > max_len:
        errors[field] = f"Máximo {max_len} caracteres"
        return None
    return s


def _number(value: Any, field: str, errors: dict[str, str], *, integer: bool = False) -> float | None:
    if isinstance(value, bool):  # bool is subclass of int -- reject
        errors[field] = "Informe um número"
        return None
    if not isinstance(value, (int, float)):
        errors[field] = "Informe um número"
        return None
    if integer and value != int(value):
        errors[field] = "Use número inteiro"
        return None
    return float(value)


def validate_desocupacao(payload: dict[str, Any]) -> DesocupacaoInput:
    errors: dict[str, str] = {}

    cidade = _str(payload.get("cidade"), "cidade", errors, 2, 80)
    edificio = _str(payload.get("edificio"), "edificio", errors, 2, 120)
    numero_apto = _str(payload.get("numeroApto"), "numeroApto", errors, 1, 20)

    area = _number(payload.get("areaPrivativa"), "areaPrivativa", errors)
    if area is not None and area <= 0:
        errors["areaPrivativa"] = "Deve ser maior que zero"
        area = None

    tipologia = _str(payload.get("tipologia"), "tipologia", errors, 1, 60)

    uso_raw = payload.get("uso")
    if uso_raw not in ALLOWED_USOS:
        errors["uso"] = f"Use um de: {', '.join(sorted(ALLOWED_USOS))}"
        uso = None
    else:
        uso = uso_raw

    status_evento = _str(payload.get("statusEvento"), "statusEvento", errors, 1, 40)
    data_evento = _parse_date(payload.get("dataEvento"), "dataEvento", errors)
    data_inicio_contrato = _parse_date(
        payload.get("dataInicioContrato"),
        "dataInicioContrato",
        errors,
    )
    if data_evento and data_inicio_contrato and data_evento < data_inicio_contrato:
        errors["dataEvento"] = "Data do evento deve ser >= data de início do contrato"

    valor_aluguel = _number(payload.get("valorAluguel"), "valorAluguel", errors)
    if valor_aluguel is not None and valor_aluguel < 0:
        errors["valorAluguel"] = "Não pode ser negativo"
        valor_aluguel = None

    dias_vacancia = _number(payload.get("diasVacancia"), "diasVacancia", errors, integer=True)
    if dias_vacancia is not None and dias_vacancia < 0:
        errors["diasVacancia"] = "Não pode ser negativo"
        dias_vacancia = None

    motivo = _str(payload.get("motivoDesocupacao"), "motivoDesocupacao", errors, 3, 500)

    mes = _number(payload.get("mes"), "mes", errors, integer=True)
    if mes is not None and not (1 <= mes <= 12):
        errors["mes"] = "Mês entre 1 e 12"
        mes = None

    ano = _number(payload.get("ano"), "ano", errors, integer=True)
    current_year = date.today().year
    if ano is not None and not (2000 <= ano <= current_year + 1):
        errors["ano"] = "Ano inválido"
        ano = None

    if errors:
        raise ValidationError(errors)

    return DesocupacaoInput(
        cidade=cidade,  # type: ignore[arg-type]
        edificio=edificio,  # type: ignore[arg-type]
        numero_apto=numero_apto,  # type: ignore[arg-type]
        area_privativa=area,  # type: ignore[arg-type]
        tipologia=tipologia,  # type: ignore[arg-type]
        uso=uso,  # type: ignore[arg-type]
        status_evento=status_evento,  # type: ignore[arg-type]
        data_evento=data_evento,  # type: ignore[arg-type]
        data_inicio_contrato=data_inicio_contrato,  # type: ignore[arg-type]
        valor_aluguel=valor_aluguel,  # type: ignore[arg-type]
        dias_vacancia=int(dias_vacancia),  # type: ignore[arg-type]
        motivo_desocupacao=motivo,  # type: ignore[arg-type]
        mes=int(mes),  # type: ignore[arg-type]
        ano=int(ano),  # type: ignore[arg-type]
    )
