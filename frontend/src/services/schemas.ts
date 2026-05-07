import { z } from 'zod';

export const usoSchema = z.enum(['Residencial', 'Comercial']);
export const tipologiaImovelValues = ['1Q', '2Q', '3Q', '4Q', 'Sala', 'Studio'] as const;
export const mobiliadoValues = ['Sim', 'N\u00e3o'] as const;
export const statusAtualImovelValues = ['Vago', 'Locado'] as const;
export const statusEventoValues = ['Desocupacao', 'Locacao'] as const;
export const motivoDesocupacaoValues = [
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
] as const;

const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
const currentYear = new Date().getFullYear();

const emptyToUndefined = (value: unknown) => {
  if (typeof value === 'string' && value.trim() === '') return undefined;
  if (typeof value === 'number' && Number.isNaN(value)) return undefined;
  return value;
};

const optionalDateSchema = z.preprocess(
  emptyToUndefined,
  z.custom<string | undefined>(() => true),
);

const optionalMoneySchema = z.preprocess(
  emptyToUndefined,
  z.custom<number | undefined>(() => true),
);

const optionalIntegerSchema = z.preprocess(
  emptyToUndefined,
  z.custom<number | undefined>(() => true),
);

const optionalMotivoSchema = z.preprocess(
  emptyToUndefined,
  z.custom<string | undefined>(() => true),
);

export function removeAccents(value: string): string {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

export function normalizeImovelText(value: string): string {
  const text = removeAccents(value).trim().replace(/\s+/g, ' ');
  if (!text) return '';
  return text
    .split(' ')
    .map((word) => word.slice(0, 1).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

export function buildIdImovel(cidade: string, edificio: string, numeroApto: string): string {
  const normalizedCidade = normalizeImovelText(cidade);
  const normalizedEdificio = normalizeImovelText(edificio);
  const apto = numeroApto.trim();
  if (!normalizedCidade || !normalizedEdificio || !/^\d+$/.test(apto)) return '';
  return `${normalizedCidade.toUpperCase()}|${normalizedEdificio.toUpperCase()}|${apto}`;
}

export const movimentacaoSchema = z
  .object({
    idImovel: z.string().trim().min(3, 'Selecione um imovel').max(220, 'Maximo 220 caracteres'),
    cidade: z.string().trim().min(2, 'Minimo 2 caracteres').max(80, 'Maximo 80 caracteres'),
    edificio: z.string().trim().min(2, 'Minimo 2 caracteres').max(120, 'Maximo 120 caracteres'),
    numeroApto: z.string().trim().min(1, 'Obrigatorio').max(20, 'Maximo 20 caracteres'),
    areaPrivativa: z
      .number({ invalid_type_error: 'Informe um numero' })
      .positive('Deve ser maior que zero'),
    tipologia: z.string().trim().min(1, 'Obrigatorio').max(60, 'Maximo 60 caracteres'),
    uso: usoSchema,
    statusEvento: z.string().trim().min(1, 'Obrigatorio').max(40, 'Maximo 40 caracteres'),
    dataEvento: z.string().min(1, 'Obrigatorio').regex(dateRegex, 'Data invalida'),
    dataInicioContrato: optionalDateSchema,
    valorAluguel: optionalMoneySchema,
    diasVacancia: optionalIntegerSchema,
    motivoDesocupacao: optionalMotivoSchema,
    mes: z
      .number({ invalid_type_error: 'Informe um numero' })
      .int('Use numero inteiro')
      .min(1, 'Mes entre 1 e 12')
      .max(12, 'Mes entre 1 e 12'),
    ano: z
      .number({ invalid_type_error: 'Informe um numero' })
      .int('Use numero inteiro')
      .min(2000, 'Ano invalido')
      .max(currentYear + 1, 'Ano invalido'),
  })
  .superRefine((d, ctx) => {
    if (!statusEventoValues.includes(d.statusEvento as (typeof statusEventoValues)[number])) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Selecione Desocupacao ou Locacao',
        path: ['statusEvento'],
      });
    }

    if (d.statusEvento === 'Desocupacao') {
      if (!d.dataInicioContrato) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Obrigatorio',
          path: ['dataInicioContrato'],
        });
      } else if (typeof d.dataInicioContrato !== 'string' || !dateRegex.test(d.dataInicioContrato)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Data invalida',
          path: ['dataInicioContrato'],
        });
      }
      if (!d.motivoDesocupacao) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Obrigatorio',
          path: ['motivoDesocupacao'],
        });
      } else if (
        typeof d.motivoDesocupacao !== 'string' ||
        !motivoDesocupacaoValues.includes(
          d.motivoDesocupacao as (typeof motivoDesocupacaoValues)[number],
        )
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Selecione um motivo valido',
          path: ['motivoDesocupacao'],
        });
      }
    }

    if (d.statusEvento === 'Locacao') {
      if (d.valorAluguel == null) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Obrigatorio',
          path: ['valorAluguel'],
        });
      } else if (typeof d.valorAluguel !== 'number' || Number.isNaN(d.valorAluguel)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Informe um numero',
          path: ['valorAluguel'],
        });
      } else if (d.valorAluguel < 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Nao pode ser negativo',
          path: ['valorAluguel'],
        });
      }
      if (d.diasVacancia == null) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Obrigatorio',
          path: ['diasVacancia'],
        });
      } else if (typeof d.diasVacancia !== 'number' || Number.isNaN(d.diasVacancia)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Informe um numero',
          path: ['diasVacancia'],
        });
      } else if (!Number.isInteger(d.diasVacancia)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Use numero inteiro',
          path: ['diasVacancia'],
        });
      } else if (d.diasVacancia < 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Nao pode ser negativo',
          path: ['diasVacancia'],
        });
      }
    }

    if (
      d.statusEvento === 'Desocupacao' &&
      typeof d.dataInicioContrato === 'string' &&
      dateRegex.test(d.dataInicioContrato) &&
      d.dataEvento < d.dataInicioContrato
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Data do evento deve ser >= data de inicio do contrato',
        path: ['dataEvento'],
      });
    }
  })
  .transform((d) => {
    if (d.statusEvento === 'Desocupacao') {
      return {
        ...d,
        valorAluguel: undefined,
        diasVacancia: undefined,
      };
    }
    if (d.statusEvento === 'Locacao') {
      return {
        ...d,
        dataInicioContrato: undefined,
        motivoDesocupacao: undefined,
      };
    }
    return d;
  });

export type MovimentacaoForm = Omit<
  z.infer<typeof movimentacaoSchema>,
  'statusEvento' | 'motivoDesocupacao'
> & {
  statusEvento: (typeof statusEventoValues)[number];
  motivoDesocupacao?: (typeof motivoDesocupacaoValues)[number] | '';
};

export const imovelSchema = z.object({
  cidade: z.string().trim().min(2, 'Minimo 2 caracteres').max(80, 'Maximo 80 caracteres'),
  edificio: z.string().trim().min(2, 'Minimo 2 caracteres').max(120, 'Maximo 120 caracteres'),
  numeroApto: z
    .string()
    .trim()
    .min(1, 'Obrigatorio')
    .max(20, 'Maximo 20 caracteres')
    .regex(/^\d+$/, 'Use apenas numeros'),
  areaPrivativa: z
    .number({ invalid_type_error: 'Informe um numero' })
    .positive('Deve ser maior que zero'),
  tipologia: z.enum(tipologiaImovelValues),
  uso: usoSchema,
  mobiliado: z.enum(mobiliadoValues),
});

export type ImovelForm = z.infer<typeof imovelSchema>;

export const loginSchema = z.object({
  email: z.string().email('E-mail inv\u00e1lido'),
  password: z.string().min(8, 'M\u00ednimo 8 caracteres'),
});

export type LoginForm = z.infer<typeof loginSchema>;

export const newPasswordSchema = z
  .object({
    newPassword: z
      .string()
      .min(8, 'Minimo 8 caracteres')
      .regex(/[a-z]/, 'Informe ao menos uma letra minuscula')
      .regex(/[A-Z]/, 'Informe ao menos uma letra maiuscula')
      .regex(/\d/, 'Informe ao menos um numero'),
    confirmPassword: z.string().min(1, 'Confirme a nova senha'),
  })
  .refine((values) => values.newPassword === values.confirmPassword, {
    message: 'As senhas precisam ser iguais',
    path: ['confirmPassword'],
  });

export type NewPasswordForm = z.infer<typeof newPasswordSchema>;
