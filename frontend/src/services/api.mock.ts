import type { Desocupacao, DesocupacaoInput } from '../types';
import { mockAuth } from './auth.mock';
import type { ApiService } from './api';

const STORAGE_KEY = 'claud.mock.desocupacoes';

function loadAll(): Desocupacao[] {
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw ? (JSON.parse(raw) as Desocupacao[]) : [];
}

function saveAll(items: Desocupacao[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

function uuid(): string {
  if (crypto.randomUUID) return crypto.randomUUID();
  return 'xxxxxxxxxxxx4xxx'.replace(/x/g, () => Math.floor(Math.random() * 16).toString(16));
}

function toCsv(items: Desocupacao[]): string {
  const header = [
    'Cidade',
    'Edificio',
    'Numero_Apto',
    'Area_Privativa',
    'Tipologia',
    'Uso',
    'Status_Evento',
    'Data_Evento',
    'Data_Inicio_Contrato',
    'Valor_Aluguel',
    'Dias_Vacancia',
    'Motivo_Desocupacao',
    'Mes',
    'Ano',
  ];
  const escape = (v: unknown) => {
    const s = String(v ?? '');
    return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const rows = items.map((d) =>
    [
      d.cidade,
      d.edificio,
      d.numeroApto,
      d.areaPrivativa,
      d.tipologia,
      d.uso,
      d.statusEvento,
      d.dataEvento,
      d.dataInicioContrato,
      d.valorAluguel,
      d.diasVacancia,
      d.motivoDesocupacao,
      d.mes,
      d.ano,
    ]
      .map(escape)
      .join(';'),
  );
  return [header.join(';'), ...rows].join('\n');
}

export const mockApi: ApiService = {
  async createDesocupacao(input: DesocupacaoInput): Promise<Desocupacao> {
    const user = mockAuth.getCurrentUser();
    if (!user) throw new Error('Não autenticado');
    const item: Desocupacao = {
      id: uuid(),
      ...input,
      criadoPor: user.sub,
      criadoEm: new Date().toISOString(),
    };
    const all = loadAll();
    all.unshift(item);
    saveAll(all);
    return item;
  },

  async listDesocupacoes(params: { ano?: number; mes?: number } = {}): Promise<Desocupacao[]> {
    const all = loadAll();
    if (!params.ano && !params.mes) return all;
    return all.filter((d) => {
      if (params.ano && d.ano !== params.ano) return false;
      if (params.mes && d.mes !== params.mes) return false;
      return true;
    });
  },

  async exportXlsx(params: { ano?: number; mes?: number } = {}): Promise<{ url: string; filename: string }> {
    const items = await mockApi.listDesocupacoes(params);
    const csv = toCsv(items);
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const stamp = new Date().toISOString().slice(0, 10);
    const filename = `desocupacoes-${stamp}.csv`;
    return { url, filename };
  },
};
