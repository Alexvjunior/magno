import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import AppHeader from '../components/AppHeader';
import { apiService } from '../services/api';
import {
  imovelSchema,
  mobiliadoValues,
  normalizeImovelText,
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
};

type CadastroImoveisContentProps = {
  embedded?: boolean;
};

export function CadastroImoveisContent({ embedded = false }: CadastroImoveisContentProps) {
  const [items, setItems] = useState<Imovel[]>([]);
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [removingIds, setRemovingIds] = useState<Set<string>>(new Set());

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

  async function onRemove(item: Imovel) {
    const confirmed = window.confirm(
      `Remover o imovel ${item.edificio} - apto ${item.numeroApto}?`,
    );
    if (!confirmed) return;

    setServerError(null);
    setSuccess(null);
    setRemovingIds((current) => new Set(current).add(item.idImovel));
    try {
      await apiService.removeImovel(item.idImovel);
      setSuccess('Imovel removido.');
      await refresh();
    } catch (e) {
      setServerError(e instanceof Error ? e.message : 'Falha ao remover imovel');
    } finally {
      setRemovingIds((current) => {
        const next = new Set(current);
        next.delete(item.idImovel);
        return next;
      });
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
                <th>Acoes</th>
                <th>ID</th>
                <th>Cidade</th>
                <th>Edificio</th>
                <th>Apto</th>
                <th>Area</th>
                <th>Tipologia</th>
                <th>Uso</th>
                <th>Mobiliado</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const isRemoving = removingIds.has(item.idImovel);
                return (
                  <tr key={item.idImovel}>
                    <td>
                      <button
                        type="button"
                        className="btn-danger"
                        onClick={() => onRemove(item)}
                        disabled={isRemoving}
                      >
                        {isRemoving ? 'Removendo...' : 'Remover'}
                      </button>
                    </td>
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
                  </tr>
                );
              })}
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
