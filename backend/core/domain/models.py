from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Literal

Uso = Literal["Residencial", "Comercial"]
RecordStatus = Literal["ACTIVE", "DELETED"]
TipologiaImovel = Literal["1Q", "2Q", "3Q", "4Q", "Sala", "Studio"]
Mobiliado = Literal["Sim", "Não"]
StatusAtualImovel = Literal["Vago", "Locado"]
StatusEvento = Literal["Desocupacao", "Locacao"]


@dataclass(frozen=True)
class MovimentacaoInput:
    id_imovel: str
    status_evento: StatusEvento
    data_evento: date
    data_inicio_contrato: date | None
    valor_aluguel: float | None
    dias_vacancia: int | None
    motivo_desocupacao: str | None
    mes: int
    ano: int


@dataclass(frozen=True)
class Movimentacao:
    id: str
    status: RecordStatus
    id_imovel: str
    cidade: str
    edificio: str
    numero_apto: str
    area_privativa: float
    tipologia: str
    uso: Uso
    status_evento: str
    data_evento: date
    data_inicio_contrato: date | None
    valor_aluguel: float | None
    dias_vacancia: int | None
    motivo_desocupacao: str | None
    mes: int
    ano: int
    criado_por: str
    criado_em: str  # ISO timestamp

    def to_item(self) -> dict:
        d = asdict(self)
        d["data_evento"] = self.data_evento.isoformat()
        d["data_inicio_contrato"] = (
            self.data_inicio_contrato.isoformat() if self.data_inicio_contrato else None
        )
        return d

    def to_api_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "idImovel": self.id_imovel,
            "cidade": self.cidade,
            "edificio": self.edificio,
            "numeroApto": self.numero_apto,
            "areaPrivativa": self.area_privativa,
            "tipologia": self.tipologia,
            "uso": self.uso,
            "statusEvento": self.status_evento,
            "dataEvento": self.data_evento.isoformat(),
            "dataInicioContrato": (
                self.data_inicio_contrato.isoformat() if self.data_inicio_contrato else None
            ),
            "valorAluguel": self.valor_aluguel,
            "diasVacancia": self.dias_vacancia,
            "motivoDesocupacao": self.motivo_desocupacao,
            "mes": self.mes,
            "ano": self.ano,
            "criadoPor": self.criado_por,
            "criadoEm": self.criado_em,
        }


DesocupacaoInput = MovimentacaoInput
Desocupacao = Movimentacao


@dataclass(frozen=True)
class ImovelInput:
    id_imovel: str
    cidade: str
    edificio: str
    numero_apto: str
    area_privativa: float
    tipologia: TipologiaImovel
    uso: Uso
    mobiliado: Mobiliado


@dataclass(frozen=True)
class Imovel:
    id_imovel: str
    cidade: str
    edificio: str
    numero_apto: str
    area_privativa: float
    tipologia: TipologiaImovel
    uso: Uso
    mobiliado: Mobiliado
    criado_por: str
    criado_em: str  # ISO timestamp
    status: RecordStatus = "ACTIVE"

    def to_item(self) -> dict:
        return asdict(self)

    def to_api_dict(self) -> dict:
        return {
            "idImovel": self.id_imovel,
            "status": self.status,
            "cidade": self.cidade,
            "edificio": self.edificio,
            "numeroApto": self.numero_apto,
            "areaPrivativa": self.area_privativa,
            "tipologia": self.tipologia,
            "uso": self.uso,
            "mobiliado": self.mobiliado,
            "criadoPor": self.criado_por,
            "criadoEm": self.criado_em,
        }
