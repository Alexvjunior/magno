import { describe, expect, it } from 'vitest';
import {
  buildIdImovel,
  imovelSchema,
  loginSchema,
  motivoDesocupacaoValues,
  movimentacaoSchema,
  newPasswordSchema,
  normalizeImovelText,
  removeAccents,
} from './schemas';

const goodMovimentacao = {
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
  valorAluguel: 0,
  diasVacancia: 0,
  motivoDesocupacao: 'Mudança geográfica',
  mes: 1,
  ano: new Date().getFullYear() + 1,
} as const;

const goodImovel = {
  cidade: 'Balneario Camboriu',
  edificio: 'Plaza Mediterraneo',
  numeroApto: '326',
  areaPrivativa: 72.5,
  tipologia: '2Q',
  uso: 'Residencial',
  mobiliado: 'Sim',
} as const;

describe('schemas', () => {
  it('normalizes text and builds stable imovel ids', () => {
    expect(removeAccents('Balneário Camboriú')).toBe('Balneario Camboriu');
    expect(normalizeImovelText('  plaza   mediterrâneo  ')).toBe('Plaza Mediterraneo');
    expect(buildIdImovel('balneário camboriú', 'plaza mediterrâneo', ' 326 ')).toBe(
      'BALNEARIO CAMBORIU|PLAZA MEDITERRANEO|326',
    );
    expect(buildIdImovel('Balneario', 'Plaza', '326A')).toBe('');
  });

  it('accepts valid movimentacao edge values and rejects invalid fields', () => {
    const parsed = movimentacaoSchema.parse({ ...goodMovimentacao, mes: 12 });
    expect(parsed).toMatchObject({ mes: 12 });
    expect(parsed.valorAluguel).toBeUndefined();
    expect(parsed.diasVacancia).toBeUndefined();

    const result = movimentacaoSchema.safeParse({
      ...goodMovimentacao,
      cidade: ' ',
      areaPrivativa: true,
      mes: 13,
      ano: 1999,
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      const paths = result.error.issues.map((issue) => issue.path.join('.'));
      expect(paths).toEqual(expect.arrayContaining(['cidade', 'areaPrivativa', 'mes', 'ano']));
    }

    const dateOrder = movimentacaoSchema.safeParse({
      ...goodMovimentacao,
      dataEvento: '2023-01-01',
      dataInicioContrato: '2024-01-01',
    });
    expect(dateOrder.success).toBe(false);
    if (!dateOrder.success) {
      expect(dateOrder.error.issues.map((issue) => issue.path.join('.'))).toContain('dataEvento');
    }
  });

  it('requires conditional movimentacao fields by status evento', () => {
    const desocupacao = movimentacaoSchema.safeParse({
      ...goodMovimentacao,
      dataInicioContrato: '',
      valorAluguel: undefined,
      diasVacancia: undefined,
      motivoDesocupacao: '',
    });
    expect(desocupacao.success).toBe(false);
    if (!desocupacao.success) {
      expect(desocupacao.error.issues.map((issue) => issue.path.join('.'))).toEqual(
        expect.arrayContaining(['dataInicioContrato', 'motivoDesocupacao']),
      );
    }

    const locacao = movimentacaoSchema.safeParse({
      ...goodMovimentacao,
      statusEvento: 'Locacao',
      dataInicioContrato: '',
      valorAluguel: undefined,
      diasVacancia: undefined,
      motivoDesocupacao: '',
    });
    expect(locacao.success).toBe(false);
    if (!locacao.success) {
      expect(locacao.error.issues.map((issue) => issue.path.join('.'))).toEqual(
        expect.arrayContaining(['valorAluguel', 'diasVacancia']),
      );
    }

    expect(
      movimentacaoSchema.safeParse({
        ...goodMovimentacao,
        statusEvento: 'Locacao',
        dataInicioContrato: 'not-a-date',
        motivoDesocupacao: 'Texto livre invalido',
      }).success,
    ).toBe(true);
  });

  it('accepts only the configured desocupacao motives', () => {
    expect(motivoDesocupacaoValues).toEqual([
      'Barulho',
      'Comprou um imóvel',
      'Desacerto comercial',
      'Desconhecido',
      'Dificuldade financeira',
      'Divórcio',
      'Exoneração garantidora',
      'Falta manutenção áreas comuns',
      'Inquilino faleceu',
      'Mudança de sede física',
      'Mudança emprego',
      'Mudança geográfica',
      'Mudou para sala 712',
      'Mudou-se para sala maior',
      'Mudou-se para uma casa',
      'Problemas de saúde',
      'Transferência do trabalho',
    ]);

    expect(
      movimentacaoSchema.safeParse({
        ...goodMovimentacao,
        motivoDesocupacao: 'Mudança geográfica',
      }).success,
    ).toBe(true);

    const result = movimentacaoSchema.safeParse({
      ...goodMovimentacao,
      motivoDesocupacao: 'Mudou de estado',
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues.map((issue) => issue.path.join('.'))).toContain(
        'motivoDesocupacao',
      );
    }
  });

  it('validates imovel contract and numeric bounds', () => {
    expect(imovelSchema.parse(goodImovel)).toMatchObject({
      numeroApto: '326',
      areaPrivativa: 72.5,
    });

    const result = imovelSchema.safeParse({
      ...goodImovel,
      numeroApto: '326A',
      areaPrivativa: 0,
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      const paths = result.error.issues.map((issue) => issue.path.join('.'));
      expect(paths).toEqual(expect.arrayContaining(['numeroApto', 'areaPrivativa']));
    }
  });

  it('validates login and new password flows', () => {
    expect(loginSchema.safeParse({ email: 'bad', password: '12345678' }).success).toBe(false);
    expect(loginSchema.safeParse({ email: 'user@example.com', password: '12345678' }).success).toBe(true);
    expect(
      newPasswordSchema.safeParse({
        newPassword: 'Password1',
        confirmPassword: 'Password1',
      }).success,
    ).toBe(true);
    expect(
      newPasswordSchema.safeParse({
        newPassword: 'password',
        confirmPassword: 'different',
      }).success,
    ).toBe(false);
  });
});
