import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mockApi } from './api.mock';
import { mockAuth } from './auth.mock';

const desocupacaoInput = {
  idImovel: 'FLORIANOPOLIS|PLAZA MEDITERRANEO|326',
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
  motivoDesocupacao: 'Mudou, disse "ate logo"; linha 2',
  mes: 7,
  ano: 2025,
} as const;

const imovelInput = {
  cidade: ' florianópolis ',
  edificio: ' plaza   mediterrâneo ',
  numeroApto: ' 326 ',
  areaPrivativa: 72.5,
  tipologia: '2Q',
  uso: 'Residencial',
  mobiliado: 'Sim',
} as const;

describe('mockApi', () => {
  beforeEach(async () => {
    await mockAuth.login('user@example.com', 'password1');
  });

  it('requires an authenticated mock user', async () => {
    await mockAuth.logout();

    await expect(mockApi.createDesocupacao(desocupacaoInput)).rejects.toThrow('autenticado');
    await expect(mockApi.createImovel(imovelInput)).rejects.toThrow('autenticado');
  });

  it('creates, filters, removes and hides deleted desocupacoes', async () => {
    await mockApi.createImovel(imovelInput);
    const created = await mockApi.createDesocupacao(desocupacaoInput);

    expect(created.status).toBe('ACTIVE');
    expect(await mockApi.listDesocupacoes()).toHaveLength(1);
    expect(await mockApi.listDesocupacoes({ ano: 2025, mes: 7 })).toHaveLength(1);
    expect(await mockApi.listDesocupacoes({ ano: 2024 })).toHaveLength(0);

    await expect(mockApi.removeDesocupacao('missing', '2025-07-03')).rejects.toThrow(
      'Desocupacao nao encontrada',
    );
    await mockApi.removeDesocupacao(created.id, created.dataEvento);
    expect(await mockApi.listDesocupacoes()).toHaveLength(0);
  });

  it('exports filtered desocupacoes as escaped CSV blob', async () => {
    const createObjectURL = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:csv');
    await mockApi.createImovel(imovelInput);
    await mockApi.createDesocupacao(desocupacaoInput);

    const exportResult = await mockApi.exportXlsx({ ano: 2025, mes: 7 });

    expect(exportResult.url).toBe('blob:csv');
    expect(exportResult.filename).toMatch(/^desocupacoes-\d{4}-\d{2}-\d{2}\.csv$/);
    const blob = createObjectURL.mock.calls[0]?.[0] as unknown as Blob;
    await expect(blob.text()).resolves.toContain('"Mudou, disse ""ate logo""; linha 2"');
  });

  it('creates normalized imoveis, rejects duplicates and sorts newest first', async () => {
    const first = await mockApi.createImovel(imovelInput);
    expect(first).toMatchObject({
      idImovel: 'FLORIANOPOLIS|PLAZA MEDITERRANEO|326',
      cidade: 'Florianopolis',
      edificio: 'Plaza Mediterraneo',
      numeroApto: '326',
    });

    await expect(mockApi.createImovel(imovelInput)).rejects.toThrow('Este imovel ja foi cadastrado.');

    const second = await mockApi.createImovel({
      ...imovelInput,
      cidade: 'Sao Jose',
      edificio: 'Residencial Ilha',
      numeroApto: '1201',
    });

    expect((await mockApi.listImoveis()).map((item) => item.idImovel)).toEqual([
      second.idImovel,
      first.idImovel,
    ]);
  });
});
