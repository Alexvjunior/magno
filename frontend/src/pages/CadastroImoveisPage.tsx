import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import AppHeader from '../components/AppHeader';
import { apiService } from '../services/api';
import {
  imovelSchema,
  mobiliadoValues,
  normalizeImovelText,
  statusAtualImovelValues,
  tipologiaImovelValues,
  type ImovelForm,
} from '../services/schemas';
import type { Imovel, ImovelInput } from '../types';

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
  const [items, setItems] = useState<Imovel[]>([]);
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ImovelForm>({
    resolver: zodResolver(imovelSchema),
    defaultValues: emptyValues,
  });

  async function refresh() {
    try {
      const list = await apiService.listImoveis();
      setItems(list.slice(0, 20));
    } catch (e) {
      setServerError(e instanceof Error ? e.message : 'Falha ao carregar lista de imoveis');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

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
      refresh();
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
              <label htmlFor="numeroAptoImovel">Numero do apto *</label>
              <input id="numeroAptoImovel" inputMode="numeric" {...register('numeroApto')} />
              {errors.numeroApto && (
                <span className="field-error">{errors.numeroApto.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="areaPrivativaImovel">Area privativa (m2) *</label>
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
              <label htmlFor="statusAtualImovel">Status atual *</label>
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
              <label htmlFor="valorAluguelAtualImovel">Valor do aluguel atual (R$) *</label>
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
              <label htmlFor="dataUltimaLocacaoImovel">Data da ultima locacao *</label>
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
              <label htmlFor="dataUltimaDesocupacaoImovel">Data da ultima desocupacao *</label>
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
              <label htmlFor="diasVacanciaAtualImovel">Dias de vacancia atual *</label>
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

      <div className="section-title">
        <h2>Ultimos imoveis ({items.length})</h2>
      </div>

      <div className="card table-card">
        {items.length === 0 ? (
          <div className="empty">Nenhum imovel ainda. Cadastre o primeiro acima.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Cidade</th>
                <th>Edificio</th>
                <th>Apto</th>
                <th>Area</th>
                <th>Tipologia</th>
                <th>Uso</th>
                <th>Mobiliado</th>
                <th>Status</th>
                <th>Aluguel</th>
                <th>Ult. Locacao</th>
                <th>Ult. Desocupacao</th>
                <th>Dias Vac.</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.idImovel}>
                  <td title={item.idImovel}>
                    {item.idImovel.length > 44
                      ? `${item.idImovel.slice(0, 44)}...`
                      : item.idImovel}
                  </td>
                  <td>{item.cidade}</td>
                  <td>{item.edificio}</td>
                  <td>{item.numeroApto}</td>
                  <td>{item.areaPrivativa.toFixed(2)}</td>
                  <td>{item.tipologia}</td>
                  <td>{item.uso}</td>
                  <td>{item.mobiliado}</td>
                  <td>{item.statusAtual}</td>
                  <td>{item.valorAluguelAtual.toFixed(2)}</td>
                  <td>{item.dataUltimaLocacao}</td>
                  <td>{item.dataUltimaDesocupacao}</td>
                  <td>{item.diasVacanciaAtual}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
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
