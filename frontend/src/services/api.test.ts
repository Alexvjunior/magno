import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mockAuth } from './auth.mock';
import { HttpApi } from './api';

const input = {
  idImovel: 'FLORIANOPOLIS|TOP VISION RESIDENCE|1227',
  cidade: 'Florianopolis',
  edificio: 'Top Vision Residence',
  numeroApto: '1227',
  areaPrivativa: 68.78,
  tipologia: '2 dormitorios',
  uso: 'Residencial',
  statusEvento: 'Desocupacao',
  dataEvento: '2025-07-03',
  dataInicioContrato: '2023-10-24',
  valorAluguel: 2500.5,
  diasVacancia: 12,
  motivoDesocupacao: 'Mudança geográfica',
  mes: 7,
  ano: 2025,
} as const;

describe('HttpApi', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(vi.fn());
  });

  it('sends bearer token, trims base url and serializes create body', async () => {
    await mockAuth.login('user@example.com', 'password1');
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ id: 'mov-1' }), { status: 201 }));

    const api = new HttpApi('https://api.example.com/');
    await expect(api.createMovimentacao(input)).resolves.toEqual({ id: 'mov-1' });

    expect(fetch).toHaveBeenCalledWith(
      'https://api.example.com/movimentacoes',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(input),
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          Authorization: expect.stringMatching(/^Bearer mock\./),
        }),
      }),
    );
  });

  it('builds query strings and delete paths', async () => {
    const api = new HttpApi('https://api.example.com');
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ url: 'u', filename: 'f' }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 'a/b', status: 'DELETED' }), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ idImovel: 'CITY|BUILDING|101', status: 'DELETED' }), {
          status: 200,
        }),
      );

    await api.listMovimentacoes({ ano: 2025, mes: 7 });
    await api.exportXlsx({ ano: 2025, mes: 7 });
    await api.removeMovimentacao('a/b', '2025-07-03');
    await api.removeImovel('CITY|BUILDING|101');

    expect(vi.mocked(fetch).mock.calls.map((call) => call[0])).toEqual([
      'https://api.example.com/movimentacoes?ano=2025&mes=7',
      'https://api.example.com/movimentacoes/export?ano=2025&mes=7',
      'https://api.example.com/movimentacoes/a%2Fb?dataEvento=2025-07-03',
      'https://api.example.com/imoveis/CITY%7CBUILDING%7C101',
    ]);
  });

  it('parses json error messages, validation errors and raw response text', async () => {
    const api = new HttpApi('https://api.example.com');
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify({ message: 'Falha direta' }), { status: 409 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ errors: { cidade: 'Obrigatorio', mes: 'Mes invalido' } }), {
          status: 422,
        }),
      )
      .mockResolvedValueOnce(new Response('gateway down', { status: 502 }));

    await expect(api.listImoveis()).rejects.toThrow('Falha direta');
    await expect(api.listImoveis()).rejects.toThrow('Obrigatorio; Mes invalido');
    await expect(api.listImoveis()).rejects.toThrow('HTTP 502: gateway down');
  });

  it('omits authorization header when no user is stored', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

    await new HttpApi('https://api.example.com').listImoveis();

    expect(fetch).toHaveBeenCalledWith(
      'https://api.example.com/imoveis',
      expect.objectContaining({
        headers: { 'Content-Type': 'application/json' },
      }),
    );
  });
});
