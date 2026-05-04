from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Literal

Uso = Literal["Residencial", "Comercial"]


@dataclass(frozen=True)
class DesocupacaoInput:
    cidade: str
    edificio: str
    numero_apto: str
    area_privativa: float
    tipologia: str
    uso: Uso
    status_evento: str
    data_evento: date
    data_inicio_contrato: date
    valor_aluguel: float
    dias_vacancia: int
    motivo_desocupacao: str
    mes: int
    ano: int


@dataclass(frozen=True)
class Desocupacao:
    id: str
    cidade: str
    edificio: str
    numero_apto: str
    area_privativa: float
    tipologia: str
    uso: Uso
    status_evento: str
    data_evento: date
    data_inicio_contrato: date
    valor_aluguel: float
    dias_vacancia: int
    motivo_desocupacao: str
    mes: int
    ano: int
    criado_por: str
    criado_em: str  # ISO timestamp

    def to_item(self) -> dict:
        d = asdict(self)
        d["data_evento"] = self.data_evento.isoformat()
        d["data_inicio_contrato"] = self.data_inicio_contrato.isoformat()
        return d

    def to_api_dict(self) -> dict:
        return {
            "id": self.id,
            "cidade": self.cidade,
            "edificio": self.edificio,
            "numeroApto": self.numero_apto,
            "areaPrivativa": self.area_privativa,
            "tipologia": self.tipologia,
            "uso": self.uso,
            "statusEvento": self.status_evento,
            "dataEvento": self.data_evento.isoformat(),
            "dataInicioContrato": self.data_inicio_contrato.isoformat(),
            "valorAluguel": self.valor_aluguel,
            "diasVacancia": self.dias_vacancia,
            "motivoDesocupacao": self.motivo_desocupacao,
            "mes": self.mes,
            "ano": self.ano,
            "criadoPor": self.criado_por,
            "criadoEm": self.criado_em,
        }
