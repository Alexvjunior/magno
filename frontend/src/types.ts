export type Uso = 'Residencial' | 'Comercial';
export type RecordStatus = 'ACTIVE' | 'DELETED';
export type TipologiaImovel = '1Q' | '2Q' | '3Q' | '4Q' | 'Sala' | 'Studio';
export type Mobiliado = 'Sim' | 'Não';
export type StatusAtualImovel = 'Vago' | 'Locado';
export type StatusEvento = 'Desocupacao' | 'Locacao';

export interface DesocupacaoInput {
  idImovel: string;
  cidade: string;
  edificio: string;
  numeroApto: string;
  areaPrivativa: number;
  tipologia: string;
  uso: Uso;
  statusEvento: StatusEvento;
  dataEvento: string;          // ISO yyyy-mm-dd
  dataInicioContrato: string;  // ISO yyyy-mm-dd
  valorAluguel: number;
  diasVacancia: number;
  motivoDesocupacao: string;
  mes: number;
  ano: number;
}

export interface Desocupacao extends DesocupacaoInput {
  id: string;
  status: RecordStatus;
  criadoPor: string;
  criadoEm: string; // ISO timestamp
}

export interface ImovelInput {
  cidade: string;
  edificio: string;
  numeroApto: string;
  areaPrivativa: number;
  tipologia: TipologiaImovel;
  uso: Uso;
  mobiliado: Mobiliado;
}

export interface Imovel extends ImovelInput {
  idImovel: string;
  criadoPor: string;
  criadoEm: string; // ISO timestamp
}

export interface AuthUser {
  sub: string;
  email: string;
  name?: string;
  token: string;
}
