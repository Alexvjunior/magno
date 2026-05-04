import { z } from 'zod';

export const usoSchema = z.enum(['Residencial', 'Comercial']);

const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
const currentYear = new Date().getFullYear();

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
