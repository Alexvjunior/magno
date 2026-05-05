export type Uso = 'Residencial' | 'Comercial';
export type RecordStatus = 'ACTIVE' | 'DELETED';

export interface DesocupacaoInput {
  cidade: string;
  edificio: string;
  numeroApto: string;
  areaPrivativa: number;
  tipologia: string;
  uso: Uso;
  statusEvento: string;
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

export interface AuthUser {
  sub: string;
  email: string;
  name?: string;
  token: string;
}
