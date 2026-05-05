import { z } from 'zod';

export const usoSchema = z.enum(['Residencial', 'Comercial']);
export const tipologiaImovelValues = ['1Q', '2Q', '3Q', '4Q', 'Sala', 'Studio'] as const;
export const mobiliadoValues = ['Sim', 'Não'] as const;
export const statusAtualImovelValues = ['Vago', 'Locado'] as const;

const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
const currentYear = new Date().getFullYear();

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

export const desocupacaoSchema = z
  .object({
    cidade: z
      .string()
      .trim()
      .min(2, 'Mínimo 2 caracteres')
      .max(80, 'Máximo 80 caracteres'),
    edificio: z
      .string()
      .trim()
      .min(2, 'Mínimo 2 caracteres')
      .max(120, 'Máximo 120 caracteres'),
    numeroApto: z
      .string()
      .trim()
      .min(1, 'Obrigatório')
      .max(20, 'Máximo 20 caracteres'),
    areaPrivativa: z
      .number({ invalid_type_error: 'Informe um número' })
      .positive('Deve ser maior que zero'),
    tipologia: z
      .string()
      .trim()
      .min(1, 'Obrigatório')
      .max(60, 'Máximo 60 caracteres'),
    uso: usoSchema,
    statusEvento: z
      .string()
      .trim()
      .min(1, 'Obrigatório')
      .max(40, 'Máximo 40 caracteres'),
    dataEvento: z
      .string()
      .min(1, 'Obrigatório')
      .regex(dateRegex, 'Data inválida'),
    dataInicioContrato: z
      .string()
      .min(1, 'Obrigatório')
      .regex(dateRegex, 'Data inválida'),
    valorAluguel: z
      .number({ invalid_type_error: 'Informe um número' })
      .nonnegative('Não pode ser negativo'),
    diasVacancia: z
      .number({ invalid_type_error: 'Informe um número' })
      .int('Use número inteiro')
      .nonnegative('Não pode ser negativo'),
    motivoDesocupacao: z
      .string()
      .trim()
      .min(3, 'Mínimo 3 caracteres')
      .max(500, 'Máximo 500 caracteres'),
    mes: z
      .number({ invalid_type_error: 'Informe um número' })
      .int('Use número inteiro')
      .min(1, 'Mês entre 1 e 12')
      .max(12, 'Mês entre 1 e 12'),
    ano: z
      .number({ invalid_type_error: 'Informe um número' })
      .int('Use número inteiro')
      .min(2000, 'Ano inválido')
      .max(currentYear + 1, 'Ano inválido'),
  })
  .refine((d) => d.dataEvento >= d.dataInicioContrato, {
    message: 'Data do evento deve ser ≥ data de início do contrato',
    path: ['dataEvento'],
  });

export type DesocupacaoForm = z.infer<typeof desocupacaoSchema>;

export const imovelSchema = z.object({
  cidade: z
    .string()
    .trim()
    .min(2, 'Minimo 2 caracteres')
    .max(80, 'Maximo 80 caracteres'),
  edificio: z
    .string()
    .trim()
    .min(2, 'Minimo 2 caracteres')
    .max(120, 'Maximo 120 caracteres'),
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
  statusAtual: z.enum(statusAtualImovelValues),
  valorAluguelAtual: z
    .number({ invalid_type_error: 'Informe um numero' })
    .nonnegative('Nao pode ser negativo'),
  dataUltimaLocacao: z
    .string()
    .min(1, 'Obrigatorio')
    .regex(dateRegex, 'Data invalida'),
  dataUltimaDesocupacao: z
    .string()
    .min(1, 'Obrigatorio')
    .regex(dateRegex, 'Data invalida'),
  diasVacanciaAtual: z
    .number({ invalid_type_error: 'Informe um numero' })
    .int('Use numero inteiro')
    .min(0, 'Nao pode ser negativo')
    .max(999, 'Maximo 3 digitos'),
});

export type ImovelForm = z.infer<typeof imovelSchema>;

export const loginSchema = z.object({
  email: z.string().email('E-mail inválido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
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
