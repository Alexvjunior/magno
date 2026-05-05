import { describe, expect, it } from 'vitest';
import {
  buildIdImovel,
  desocupacaoSchema,
  imovelSchema,
  loginSchema,
  newPasswordSchema,
  normalizeImovelText,
  removeAccents,
} from './schemas';

const goodDesocupacao = {
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
  motivoDesocupacao: 'Mudou de estado',
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
  statusAtual: 'Vago',
  valorAluguelAtual: 0,
  dataUltimaLocacao: '2025-02-10',
  dataUltimaDesocupacao: '2025-05-01',
  diasVacanciaAtual: 0,
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

  it('accepts valid desocupacao edge values and rejects invalid fields', () => {
    expect(desocupacaoSchema.parse({ ...goodDesocupacao, mes: 12 })).toMatchObject({
      mes: 12,
      valorAluguel: 0,
      diasVacancia: 0,
    });

    const result = desocupacaoSchema.safeParse({
      ...goodDesocupacao,
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

    const dateOrder = desocupacaoSchema.safeParse({
      ...goodDesocupacao,
      dataEvento: '2023-01-01',
      dataInicioContrato: '2024-01-01',
    });
    expect(dateOrder.success).toBe(false);
    if (!dateOrder.success) {
      expect(dateOrder.error.issues.map((issue) => issue.path.join('.'))).toContain('dataEvento');
    }
  });

  it('validates imovel contract and numeric bounds', () => {
    expect(imovelSchema.parse({ ...goodImovel, diasVacanciaAtual: 999 })).toMatchObject({
      numeroApto: '326',
      valorAluguelAtual: 0,
      diasVacanciaAtual: 999,
    });

    const result = imovelSchema.safeParse({
      ...goodImovel,
      numeroApto: '326A',
      areaPrivativa: 0,
      valorAluguelAtual: -1,
      diasVacanciaAtual: 1000,
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      const paths = result.error.issues.map((issue) => issue.path.join('.'));
      expect(paths).toEqual(
        expect.arrayContaining(['numeroApto', 'areaPrivativa', 'valorAluguelAtual', 'diasVacanciaAtual']),
      );
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
