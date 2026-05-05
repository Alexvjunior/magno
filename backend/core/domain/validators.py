"""Validators for the Desocupacao input payload.

Returns a cleaned dataclass or raises ValidationError. The accepted payload
mirrors the React form contract in frontend/src/types.ts.
"""
from __future__ import annotations

import unicodedata
from datetime import date, datetime
from typing import Any

from .models import DesocupacaoInput, ImovelInput

ALLOWED_USOS = {"Residencial", "Comercial"}
ALLOWED_TIPOLOGIAS_IMOVEL = {"1Q", "2Q", "3Q", "4Q", "Sala", "Studio"}
ALLOWED_MOBILIADO = {"Sim", "Não"}
ALLOWED_STATUS_ATUAL_IMOVEL = {"Vago", "Locado"}


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


def remove_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def normalize_imovel_text(value: str) -> str:
    text = " ".join(remove_accents(value).strip().split())
    return " ".join(word[:1].upper() + word[1:].lower() for word in text.split(" "))


def build_id_imovel(cidade: str, edificio: str, numero_apto: str) -> str:
    return f"{cidade.upper()}|{edificio.upper()}|{numero_apto}"


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


def validate_imovel(payload: dict[str, Any]) -> ImovelInput:
    errors: dict[str, str] = {}

    cidade_raw = _str(payload.get("cidade"), "cidade", errors, 2, 80)
    edificio_raw = _str(payload.get("edificio"), "edificio", errors, 2, 120)
    cidade = normalize_imovel_text(cidade_raw) if cidade_raw else None
    edificio = normalize_imovel_text(edificio_raw) if edificio_raw else None

    numero_apto = _str(payload.get("numeroApto"), "numeroApto", errors, 1, 20)
    if numero_apto is not None and not numero_apto.isdigit():
        errors["numeroApto"] = "Use apenas numeros"
        numero_apto = None

    area = _number(payload.get("areaPrivativa"), "areaPrivativa", errors)
    if area is not None and area <= 0:
        errors["areaPrivativa"] = "Deve ser maior que zero"
        area = None

    tipologia_raw = payload.get("tipologia")
    if tipologia_raw not in ALLOWED_TIPOLOGIAS_IMOVEL:
        errors["tipologia"] = f"Use um de: {', '.join(sorted(ALLOWED_TIPOLOGIAS_IMOVEL))}"
        tipologia = None
    else:
        tipologia = tipologia_raw

    uso_raw = payload.get("uso")
    if uso_raw not in ALLOWED_USOS:
        errors["uso"] = f"Use um de: {', '.join(sorted(ALLOWED_USOS))}"
        uso = None
    else:
        uso = uso_raw

    mobiliado_raw = payload.get("mobiliado")
    if mobiliado_raw not in ALLOWED_MOBILIADO:
        errors["mobiliado"] = f"Use um de: {', '.join(sorted(ALLOWED_MOBILIADO))}"
        mobiliado = None
    else:
        mobiliado = mobiliado_raw

    status_atual_raw = payload.get("statusAtual")
    if status_atual_raw not in ALLOWED_STATUS_ATUAL_IMOVEL:
        errors["statusAtual"] = f"Use um de: {', '.join(sorted(ALLOWED_STATUS_ATUAL_IMOVEL))}"
        status_atual = None
    else:
        status_atual = status_atual_raw

    valor_aluguel_atual = _number(
        payload.get("valorAluguelAtual"),
        "valorAluguelAtual",
        errors,
    )
    if valor_aluguel_atual is not None and valor_aluguel_atual < 0:
        errors["valorAluguelAtual"] = "Nao pode ser negativo"
        valor_aluguel_atual = None

    data_ultima_locacao = _parse_date(
        payload.get("dataUltimaLocacao"),
        "dataUltimaLocacao",
        errors,
    )
    data_ultima_desocupacao = _parse_date(
        payload.get("dataUltimaDesocupacao"),
        "dataUltimaDesocupacao",
        errors,
    )

    dias_vacancia_atual = _number(
        payload.get("diasVacanciaAtual"),
        "diasVacanciaAtual",
        errors,
        integer=True,
    )
    if dias_vacancia_atual is not None and not (0 <= dias_vacancia_atual <= 999):
        errors["diasVacanciaAtual"] = "Use numero entre 0 e 999"
        dias_vacancia_atual = None

    if errors:
        raise ValidationError(errors)

    id_imovel = build_id_imovel(cidade, edificio, numero_apto)  # type: ignore[arg-type]

    return ImovelInput(
        id_imovel=id_imovel,
        cidade=cidade,  # type: ignore[arg-type]
        edificio=edificio,  # type: ignore[arg-type]
        numero_apto=numero_apto,  # type: ignore[arg-type]
        area_privativa=area,  # type: ignore[arg-type]
        tipologia=tipologia,  # type: ignore[arg-type]
        uso=uso,  # type: ignore[arg-type]
        mobiliado=mobiliado,  # type: ignore[arg-type]
        status_atual=status_atual,  # type: ignore[arg-type]
        valor_aluguel_atual=valor_aluguel_atual,  # type: ignore[arg-type]
        data_ultima_locacao=data_ultima_locacao,  # type: ignore[arg-type]
        data_ultima_desocupacao=data_ultima_desocupacao,  # type: ignore[arg-type]
        dias_vacancia_atual=int(dias_vacancia_atual),  # type: ignore[arg-type]
    )
