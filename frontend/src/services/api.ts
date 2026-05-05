import { env } from '../config/env';
import type { Desocupacao, DesocupacaoInput, Imovel, ImovelInput } from '../types';
import { mockApi } from './api.mock';
import { authService } from './auth';

export interface ApiService {
  createDesocupacao(input: DesocupacaoInput): Promise<Desocupacao>;
  createImovel(input: ImovelInput): Promise<Imovel>;
  listDesocupacoes(params?: { ano?: number; mes?: number }): Promise<Desocupacao[]>;
  listImoveis(): Promise<Imovel[]>;
  exportXlsx(params?: { ano?: number; mes?: number }): Promise<{ url: string; filename: string }>;
  removeDesocupacao(id: string, dataEvento: string): Promise<{ id: string; status: 'DELETED' }>;
}

export class HttpApi implements ApiService {
  private baseUrl: string;
  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const user = authService.getCurrentUser();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((init?.headers as Record<string, string>) ?? {}),
    };
    if (user?.token) headers.Authorization = `Bearer ${user.token}`;
    const res = await fetch(this.baseUrl + path, { ...init, headers });
    if (!res.ok) {
      const body = await res.text();
      let message = body ? `HTTP ${res.status}: ${body}` : `HTTP ${res.status}`;
      try {
        const parsed = JSON.parse(body) as { message?: string; errors?: Record<string, string> };
        if (parsed.message) {
          message = parsed.message;
        } else if (parsed.errors) {
          message = Object.values(parsed.errors).join('; ');
        }
      } catch {
        // Keep the raw HTTP message when the response is not JSON.
      }
      throw new Error(message);
    }
    return (await res.json()) as T;
  }

  createDesocupacao(input: DesocupacaoInput): Promise<Desocupacao> {
    return this.request<Desocupacao>('/desocupacoes', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  createImovel(input: ImovelInput): Promise<Imovel> {
    return this.request<Imovel>('/imoveis', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  listDesocupacoes(params: { ano?: number; mes?: number } = {}): Promise<Desocupacao[]> {
    const qs = new URLSearchParams();
    if (params.ano) qs.set('ano', String(params.ano));
    if (params.mes) qs.set('mes', String(params.mes));
    const suffix = qs.toString() ? `?${qs}` : '';
    return this.request<Desocupacao[]>(`/desocupacoes${suffix}`);
  }

  listImoveis(): Promise<Imovel[]> {
    return this.request<Imovel[]>('/imoveis');
  }

  exportXlsx(params: { ano?: number; mes?: number } = {}): Promise<{ url: string; filename: string }> {
    const qs = new URLSearchParams();
    if (params.ano) qs.set('ano', String(params.ano));
    if (params.mes) qs.set('mes', String(params.mes));
    const suffix = qs.toString() ? `?${qs}` : '';
    return this.request<{ url: string; filename: string }>(`/desocupacoes/export${suffix}`);
  }

  removeDesocupacao(id: string, dataEvento: string): Promise<{ id: string; status: 'DELETED' }> {
    const qs = new URLSearchParams({ dataEvento });
    return this.request<{ id: string; status: 'DELETED' }>(
      `/desocupacoes/${encodeURIComponent(id)}?${qs}`,
      { method: 'DELETE' },
    );
  }
}

export const apiService: ApiService = env.useMock ? mockApi : new HttpApi(env.apiUrl);
