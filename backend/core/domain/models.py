from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Literal

Uso = Literal["Residencial", "Comercial"]
RecordStatus = Literal["ACTIVE", "DELETED"]
TipologiaImovel = Literal["1Q", "2Q", "3Q", "4Q", "Sala", "Studio"]
Mobiliado = Literal["Sim", "Não"]
StatusAtualImovel = Literal["Vago", "Locado"]


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
    status: RecordStatus
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
            "status": self.status,
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
    status_atual: StatusAtualImovel
    valor_aluguel_atual: float
    data_ultima_locacao: date
    data_ultima_desocupacao: date
    dias_vacancia_atual: int


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
    status_atual: StatusAtualImovel
    valor_aluguel_atual: float
    data_ultima_locacao: date
    data_ultima_desocupacao: date
    dias_vacancia_atual: int
    criado_por: str
    criado_em: str  # ISO timestamp

    def to_item(self) -> dict:
        d = asdict(self)
        d["data_ultima_locacao"] = self.data_ultima_locacao.isoformat()
        d["data_ultima_desocupacao"] = self.data_ultima_desocupacao.isoformat()
        return d

    def to_api_dict(self) -> dict:
        return {
            "idImovel": self.id_imovel,
            "cidade": self.cidade,
            "edificio": self.edificio,
            "numeroApto": self.numero_apto,
            "areaPrivativa": self.area_privativa,
            "tipologia": self.tipologia,
            "uso": self.uso,
            "mobiliado": self.mobiliado,
            "statusAtual": self.status_atual,
            "valorAluguelAtual": self.valor_aluguel_atual,
            "dataUltimaLocacao": self.data_ultima_locacao.isoformat(),
            "dataUltimaDesocupacao": self.data_ultima_desocupacao.isoformat(),
            "diasVacanciaAtual": self.dias_vacancia_atual,
            "criadoPor": self.criado_por,
            "criadoEm": self.criado_em,
        }
