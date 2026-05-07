"""Validators for API input payloads.

Returns a cleaned dataclass or raises ValidationError. The accepted payload
mirrors the React form contract in frontend/src/types.ts.
"""
from __future__ import annotations

import unicodedata
from datetime import date, datetime
from typing import Any

from .models import ImovelInput, MovimentacaoInput

ALLOWED_USOS = {"Residencial", "Comercial"}
ALLOWED_TIPOLOGIAS_IMOVEL = {"1Q", "2Q", "3Q", "4Q", "Sala", "Studio"}
ALLOWED_MOBILIADO = {"Sim", "N\u00e3o"}
ALLOWED_STATUS_ATUAL_IMOVEL = {"Vago", "Locado"}
ALLOWED_STATUS_EVENTOS = {"Desocupacao", "Locacao"}
ALLOWED_MOTIVOS_DESOCUPACAO = {
    "Barulho",
    "Comprou um imóvel",
    "Desacerto comercial",
    "Desconhecido",
    "Dificuldade financeira",
    "Divórcio",
    "Exoneração garantidora",
    "Falta manutenção áreas comuns",
    "Inquilino faleceu",
    "Mudança de sede física",
    "Mudança emprego",
    "Mudança geográfica",
    "Mudou para sala 712",
    "Mudou-se para sala maior",
    "Mudou-se para uma casa",
    "Problemas de saúde",
    "Transferência do trabalho",
}


class ValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        super().__init__("Validation failed")
        self.errors = errors


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _parse_date(value: Any, field: str, errors: dict[str, str]) -> date | None:
    if not isinstance(value, str) or not value.strip():
        errors[field] = "Obrigatorio"
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        errors[field] = "Data invalida (use YYYY-MM-DD)"
        return None


def _parse_optional_date(value: Any, field: str, errors: dict[str, str]) -> date | None:
    if _is_blank(value):
        return None
    if not isinstance(value, str):
        errors[field] = "Data invalida (use YYYY-MM-DD)"
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        errors[field] = "Data invalida (use YYYY-MM-DD)"
        return None


def _str(value: Any, field: str, errors: dict[str, str], min_len: int, max_len: int) -> str | None:
    if not isinstance(value, str):
        errors[field] = "Obrigatorio"
        return None
    s = value.strip()
    if len(s) < min_len:
        errors[field] = "Obrigatorio" if min_len == 1 else f"Minimo {min_len} caracteres"
        return None
    if len(s) > max_len:
        errors[field] = f"Maximo {max_len} caracteres"
        return None
    return s


def _optional_str(
    value: Any,
    field: str,
    errors: dict[str, str],
    min_len: int,
    max_len: int,
) -> str | None:
    if _is_blank(value):
        return None
    return _str(value, field, errors, min_len, max_len)


def _number(value: Any, field: str, errors: dict[str, str], *, integer: bool = False) -> float | None:
    if isinstance(value, bool):
        errors[field] = "Informe um numero"
        return None
    if not isinstance(value, (int, float)):
        errors[field] = "Informe um numero"
        return None
    if integer and value != int(value):
        errors[field] = "Use numero inteiro"
        return None
    return float(value)


def _optional_number(
    value: Any,
    field: str,
    errors: dict[str, str],
    *,
    integer: bool = False,
) -> float | None:
    if _is_blank(value):
        return None
    return _number(value, field, errors, integer=integer)


def remove_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def normalize_imovel_text(value: str) -> str:
    text = " ".join(remove_accents(value).strip().split())
    return " ".join(word[:1].upper() + word[1:].lower() for word in text.split(" "))


def build_id_imovel(cidade: str, edificio: str, numero_apto: str) -> str:
    return f"{cidade.upper()}|{edificio.upper()}|{numero_apto}"


def validate_movimentacao(payload: dict[str, Any]) -> MovimentacaoInput:
    errors: dict[str, str] = {}

    id_imovel = _str(payload.get("idImovel"), "idImovel", errors, 3, 220)

    status_evento_raw = payload.get("statusEvento")
    if status_evento_raw not in ALLOWED_STATUS_EVENTOS:
        errors["statusEvento"] = f"Use um de: {', '.join(sorted(ALLOWED_STATUS_EVENTOS))}"
        status_evento = None
    else:
        status_evento = status_evento_raw

    data_evento = _parse_date(payload.get("dataEvento"), "dataEvento", errors)

    data_inicio_contrato = None
    valor_aluguel = None
    dias_vacancia = None
    motivo = None

    if status_evento == "Desocupacao":
        data_inicio_contrato_raw = payload.get("dataInicioContrato")
        data_inicio_contrato = _parse_optional_date(
            data_inicio_contrato_raw,
            "dataInicioContrato",
            errors,
        )
        if _is_blank(data_inicio_contrato_raw):
            errors["dataInicioContrato"] = "Obrigatorio"
        if data_evento and data_inicio_contrato and data_evento < data_inicio_contrato:
            errors["dataEvento"] = "Data do evento deve ser >= data de inicio do contrato"

        motivo_raw = payload.get("motivoDesocupacao")
        if _is_blank(motivo_raw):
            errors["motivoDesocupacao"] = "Obrigatorio"
        else:
            motivo = _optional_str(motivo_raw, "motivoDesocupacao", errors, 1, 500)
            if motivo is not None and motivo not in ALLOWED_MOTIVOS_DESOCUPACAO:
                errors["motivoDesocupacao"] = "Selecione um motivo valido"
                motivo = None
    elif status_evento == "Locacao":
        valor_aluguel_raw = payload.get("valorAluguel")
        if _is_blank(valor_aluguel_raw):
            errors["valorAluguel"] = "Obrigatorio"
        else:
            valor_aluguel = _optional_number(valor_aluguel_raw, "valorAluguel", errors)
            if valor_aluguel is not None and valor_aluguel < 0:
                errors["valorAluguel"] = "Nao pode ser negativo"
                valor_aluguel = None

        dias_vacancia_raw = payload.get("diasVacancia")
        if _is_blank(dias_vacancia_raw):
            errors["diasVacancia"] = "Obrigatorio"
        else:
            dias_vacancia = _optional_number(
                dias_vacancia_raw,
                "diasVacancia",
                errors,
                integer=True,
            )
            if dias_vacancia is not None and dias_vacancia < 0:
                errors["diasVacancia"] = "Nao pode ser negativo"
                dias_vacancia = None

    mes = _number(payload.get("mes"), "mes", errors, integer=True)
    if mes is not None and not (1 <= mes <= 12):
        errors["mes"] = "Mes entre 1 e 12"
        mes = None

    ano = _number(payload.get("ano"), "ano", errors, integer=True)
    current_year = date.today().year
    if ano is not None and not (2000 <= ano <= current_year + 1):
        errors["ano"] = "Ano invalido"
        ano = None

    if errors:
        raise ValidationError(errors)

    return MovimentacaoInput(
        id_imovel=id_imovel,  # type: ignore[arg-type]
        status_evento=status_evento,  # type: ignore[arg-type]
        data_evento=data_evento,  # type: ignore[arg-type]
        data_inicio_contrato=data_inicio_contrato,
        valor_aluguel=valor_aluguel,
        dias_vacancia=int(dias_vacancia) if dias_vacancia is not None else None,
        motivo_desocupacao=motivo,
        mes=int(mes),  # type: ignore[arg-type]
        ano=int(ano),  # type: ignore[arg-type]
    )


validate_desocupacao = validate_movimentacao


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
    )
