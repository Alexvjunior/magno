import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mockApi } from './api.mock';
import { mockAuth } from './auth.mock';

const movimentacaoInput = {
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
  motivoDesocupacao: 'Mudança geográfica',
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

    await expect(mockApi.createMovimentacao(movimentacaoInput)).rejects.toThrow('autenticado');
    await expect(mockApi.createImovel(imovelInput)).rejects.toThrow('autenticado');
  });

  it('creates, filters, removes and hides deleted movimentacoes', async () => {
    await mockApi.createImovel(imovelInput);
    const created = await mockApi.createMovimentacao(movimentacaoInput);

    expect(created.status).toBe('ACTIVE');
    expect(await mockApi.listMovimentacoes()).toHaveLength(1);
    expect(await mockApi.listMovimentacoes({ ano: 2025, mes: 7 })).toHaveLength(1);
    expect(await mockApi.listMovimentacoes({ ano: 2024 })).toHaveLength(0);

    await expect(mockApi.removeMovimentacao('missing', '2025-07-03')).rejects.toThrow(
      'Movimentacao nao encontrada',
    );
    await mockApi.removeMovimentacao(created.id, created.dataEvento);
    expect(await mockApi.listMovimentacoes()).toHaveLength(0);
  });

  it('requires a previous desocupacao before creating a locacao', async () => {
    await mockApi.createImovel(imovelInput);
    const locacaoInput = {
      ...movimentacaoInput,
      statusEvento: 'Locacao',
      dataEvento: '2025-07-04',
      dataInicioContrato: null,
      valorAluguel: 3000,
      diasVacancia: 1,
      motivoDesocupacao: null,
    } as const;

    await expect(mockApi.createMovimentacao(locacaoInput)).rejects.toThrow(
      'O imovel nao tem como ultimo registro uma desocupacao.',
    );

    await mockApi.createMovimentacao(movimentacaoInput);
    await expect(mockApi.createMovimentacao(locacaoInput)).resolves.toMatchObject({
      statusEvento: 'Locacao',
      valorAluguel: 3000,
      diasVacancia: 1,
      dataInicioContrato: null,
      motivoDesocupacao: null,
    });
  });

  it('exports filtered movimentacoes as escaped CSV blob', async () => {
    const createObjectURL = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:csv');
    await mockApi.createImovel(imovelInput);
    await mockApi.createMovimentacao(movimentacaoInput);

    const exportResult = await mockApi.exportXlsx({ ano: 2025, mes: 7 });

    expect(exportResult.url).toBe('blob:csv');
    expect(exportResult.filename).toMatch(/^movimentacoes-\d{4}-\d{2}-\d{2}\.csv$/);
    const blob = createObjectURL.mock.calls[0]?.[0] as unknown as Blob;
    await expect(blob.text()).resolves.toContain('Mudança geográfica');
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
