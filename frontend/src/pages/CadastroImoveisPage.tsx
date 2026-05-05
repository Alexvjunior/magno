import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import AppHeader from '../components/AppHeader';
import { apiService } from '../services/api';
import {
  buildIdImovel,
  imovelSchema,
  mobiliadoValues,
  normalizeImovelText,
  statusAtualImovelValues,
  tipologiaImovelValues,
  type ImovelForm,
} from '../services/schemas';
import type { ImovelInput } from '../types';

const emptyValues: ImovelForm = {
  cidade: '',
  edificio: '',
  numeroApto: '',
  areaPrivativa: undefined as unknown as number,
  tipologia: '1Q',
  uso: 'Residencial',
  mobiliado: 'Não',
  statusAtual: 'Vago',
  valorAluguelAtual: undefined as unknown as number,
  dataUltimaLocacao: '',
  dataUltimaDesocupacao: '',
  diasVacanciaAtual: undefined as unknown as number,
};

type CadastroImoveisContentProps = {
  embedded?: boolean;
};

export function CadastroImoveisContent({ embedded = false }: CadastroImoveisContentProps) {
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ImovelForm>({
    resolver: zodResolver(imovelSchema),
    defaultValues: emptyValues,
  });

  const idPreview = buildIdImovel(
    watch('cidade') ?? '',
    watch('edificio') ?? '',
    watch('numeroApto') ?? '',
  );

  async function onSubmit(values: ImovelForm) {
    setServerError(null);
    setSuccess(null);

    const input: ImovelInput = {
      ...values,
      cidade: normalizeImovelText(values.cidade),
      edificio: normalizeImovelText(values.edificio),
      numeroApto: values.numeroApto.trim(),
    };

    try {
      const created = await apiService.createImovel(input);
      setSuccess(`Imovel ${created.idImovel} cadastrado.`);
      reset(emptyValues);
    } catch (e) {
      setServerError(e instanceof Error ? e.message : 'Falha ao cadastrar imovel');
    }
  }

  return (
    <div className={embedded ? 'cadastro-content cadastro-content-embedded' : 'container'}>
      <div className="card">
        <h1>Novo imovel</h1>

        {serverError && <div className="alert alert-error">{serverError}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="row">
            <div className="field">
              <label htmlFor="idImovel">ID_Imovel</label>
              <input id="idImovel" value={idPreview} readOnly />
            </div>

            <div className="field">
              <label htmlFor="cidadeImovel">Cidade *</label>
              <input id="cidadeImovel" {...register('cidade')} />
              {errors.cidade && <span className="field-error">{errors.cidade.message}</span>}
            </div>

            <div className="field">
              <label htmlFor="edificioImovel">Edificio *</label>
              <input id="edificioImovel" {...register('edificio')} />
              {errors.edificio && <span className="field-error">{errors.edificio.message}</span>}
            </div>

            <div className="field">
              <label htmlFor="numeroAptoImovel">Numero_Apto *</label>
              <input id="numeroAptoImovel" inputMode="numeric" {...register('numeroApto')} />
              {errors.numeroApto && (
                <span className="field-error">{errors.numeroApto.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="areaPrivativaImovel">Area_Privativa (m2) *</label>
              <input
                id="areaPrivativaImovel"
                type="number"
                step="0.01"
                min={0}
                {...register('areaPrivativa', { valueAsNumber: true })}
              />
              {errors.areaPrivativa && (
                <span className="field-error">{errors.areaPrivativa.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="tipologiaImovel">Tipologia *</label>
              <select id="tipologiaImovel" {...register('tipologia')}>
                {tipologiaImovelValues.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
              {errors.tipologia && (
                <span className="field-error">{errors.tipologia.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="usoImovel">Uso *</label>
              <select id="usoImovel" {...register('uso')}>
                <option value="Residencial">Residencial</option>
                <option value="Comercial">Comercial</option>
              </select>
              {errors.uso && <span className="field-error">{errors.uso.message}</span>}
            </div>

            <div className="field">
              <label htmlFor="mobiliadoImovel">Mobiliado *</label>
              <select id="mobiliadoImovel" {...register('mobiliado')}>
                {mobiliadoValues.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
              {errors.mobiliado && (
                <span className="field-error">{errors.mobiliado.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="statusAtualImovel">Status_Atual *</label>
              <select id="statusAtualImovel" {...register('statusAtual')}>
                {statusAtualImovelValues.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
              {errors.statusAtual && (
                <span className="field-error">{errors.statusAtual.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="valorAluguelAtualImovel">Valor_Aluguel_Atual (R$) *</label>
              <input
                id="valorAluguelAtualImovel"
                type="number"
                step="0.01"
                min={0}
                {...register('valorAluguelAtual', { valueAsNumber: true })}
              />
              {errors.valorAluguelAtual && (
                <span className="field-error">{errors.valorAluguelAtual.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="dataUltimaLocacaoImovel">Data_Ultima_Locacao *</label>
              <input
                id="dataUltimaLocacaoImovel"
                type="date"
                {...register('dataUltimaLocacao')}
              />
              {errors.dataUltimaLocacao && (
                <span className="field-error">{errors.dataUltimaLocacao.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="dataUltimaDesocupacaoImovel">Data_Ultima_Desocupacao *</label>
              <input
                id="dataUltimaDesocupacaoImovel"
                type="date"
                {...register('dataUltimaDesocupacao')}
              />
              {errors.dataUltimaDesocupacao && (
                <span className="field-error">{errors.dataUltimaDesocupacao.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="diasVacanciaAtualImovel">Dias_Vacancia_Atual *</label>
              <input
                id="diasVacanciaAtualImovel"
                type="number"
                step="1"
                min={0}
                max={999}
                {...register('diasVacanciaAtual', { valueAsNumber: true })}
              />
              {errors.diasVacanciaAtual && (
                <span className="field-error">{errors.diasVacanciaAtual.message}</span>
              )}
            </div>
          </div>

          <div className="actions">
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function CadastroImoveisPage() {
  return (
    <>
      <AppHeader title="Cadastro de Imoveis" />
      <CadastroImoveisContent />
    </>
  );
}
