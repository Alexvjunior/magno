import type { Imovel, Movimentacao } from '../types';

export const movimentacaoFixture: Movimentacao = {
  id: 'mov-1',
  status: 'ACTIVE',
  idImovel: 'FLORIANOPOLIS|PLAZA MEDITERRANEO|326',
  cidade: 'Florianopolis',
  edificio: 'Plaza Mediterraneo',
  numeroApto: '326',
  areaPrivativa: 72.5,
  tipologia: '2Q',
  uso: 'Residencial',
  statusEvento: 'Desocupacao',
  dataEvento: '2025-07-03',
  dataInicioContrato: '2023-10-24',
  valorAluguel: null,
  diasVacancia: null,
  motivoDesocupacao: 'Mudança geográfica',
  mes: 7,
  ano: 2025,
  criadoPor: 'user-1',
  criadoEm: '2025-07-03T12:00:00Z',
};

export const imovelFixture: Imovel = {
  idImovel: 'FLORIANOPOLIS|PLAZA MEDITERRANEO|326',
  status: 'ACTIVE',
  cidade: 'Florianopolis',
  edificio: 'Plaza Mediterraneo',
  numeroApto: '326',
  areaPrivativa: 72.5,
  tipologia: '2Q',
  uso: 'Residencial',
  mobiliado: 'N\u00e3o',
  criadoPor: 'user-1',
  criadoEm: '2025-05-01T12:00:00Z',
};
