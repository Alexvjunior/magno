import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import AppHeader from '../components/AppHeader';
import { env } from '../config/env';
import { apiService } from '../services/api';
import { desocupacaoSchema, type DesocupacaoForm } from '../services/schemas';
import type { Desocupacao } from '../types';

const emptyValues: DesocupacaoForm = {
  cidade: '',
  edificio: '',
  numeroApto: '',
  areaPrivativa: undefined as unknown as number,
  tipologia: '',
  uso: 'Residencial',
  statusEvento: '',
  dataEvento: '',
  dataInicioContrato: '',
  valorAluguel: undefined as unknown as number,
  diasVacancia: undefined as unknown as number,
  motivoDesocupacao: '',
  mes: undefined as unknown as number,
  ano: undefined as unknown as number,
};

type CadastroContentProps = {
  embedded?: boolean;
};

export function CadastroContent({ embedded = false }: CadastroContentProps) {
  const [items, setItems] = useState<Desocupacao[]>([]);
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [removingIds, setRemovingIds] = useState<Set<string>>(new Set());

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<DesocupacaoForm>({
    resolver: zodResolver(desocupacaoSchema),
    defaultValues: emptyValues,
  });

  async function refresh() {
    try {
      const list = await apiService.listDesocupacoes();
      setItems(list.slice(0, 20));
    } catch (e) {
      setServerError(e instanceof Error ? e.message : 'Falha ao carregar lista');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onSubmit(values: DesocupacaoForm) {
    setServerError(null);
    setSuccess(null);
    try {
      await apiService.createDesocupacao(values);
      setSuccess('Desocupacao cadastrada.');
      reset(emptyValues);
      refresh();
    } catch (e) {
      setServerError(e instanceof Error ? e.message : 'Falha ao cadastrar');
    }
  }

  async function onExport() {
    setServerError(null);
    try {
      const { url, filename } = await apiService.exportXlsx();
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      setServerError(e instanceof Error ? e.message : 'Falha ao exportar');
    }
  }

  async function onRemove(item: Desocupacao) {
    const confirmed = window.confirm(
      `Remover a desocupacao de ${item.edificio} - apto ${item.numeroApto}?`,
    );
    if (!confirmed) return;

    setServerError(null);
    setSuccess(null);
    setRemovingIds((current) => new Set(current).add(item.id));
    try {
      await apiService.removeDesocupacao(item.id, item.dataEvento);
      setSuccess('Desocupacao removida.');
      await refresh();
    } catch (e) {
      setServerError(e instanceof Error ? e.message : 'Falha ao remover');
    } finally {
      setRemovingIds((current) => {
        const next = new Set(current);
        next.delete(item.id);
        return next;
      });
    }
  }

  return (
    <div className={embedded ? 'cadastro-content cadastro-content-embedded' : 'container'}>
      <div className="card">
        <h1>Nova desocupacao</h1>
        <p className="muted">Preencha os dados. Campos com * sao obrigatorios.</p>

        {serverError && <div className="alert alert-error">{serverError}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="row">
            <div className="field">
              <label htmlFor="cidade">Cidade *</label>
              <input id="cidade" {...register('cidade')} />
              {errors.cidade && <span className="field-error">{errors.cidade.message}</span>}
            </div>

            <div className="field">
              <label htmlFor="edificio">Edificio *</label>
              <input id="edificio" {...register('edificio')} />
              {errors.edificio && <span className="field-error">{errors.edificio.message}</span>}
            </div>

            <div className="field">
              <label htmlFor="numeroApto">Numero do Apto *</label>
              <input id="numeroApto" {...register('numeroApto')} />
              {errors.numeroApto && (
                <span className="field-error">{errors.numeroApto.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="areaPrivativa">Area Privativa (m2) *</label>
              <input
                id="areaPrivativa"
                type="number"
                step="0.01"
                {...register('areaPrivativa', { valueAsNumber: true })}
              />
              {errors.areaPrivativa && (
                <span className="field-error">{errors.areaPrivativa.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="tipologia">Tipologia *</label>
              <input id="tipologia" {...register('tipologia')} />
              {errors.tipologia && (
                <span className="field-error">{errors.tipologia.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="uso">Uso *</label>
              <select id="uso" {...register('uso')}>
                <option value="Residencial">Residencial</option>
                <option value="Comercial">Comercial</option>
              </select>
              {errors.uso && <span className="field-error">{errors.uso.message}</span>}
            </div>

            <div className="field">
              <label htmlFor="statusEvento">Status do Evento *</label>
              <input id="statusEvento" {...register('statusEvento')} />
              {errors.statusEvento && (
                <span className="field-error">{errors.statusEvento.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="dataEvento">Data do Evento *</label>
              <input id="dataEvento" type="date" {...register('dataEvento')} />
              {errors.dataEvento && (
                <span className="field-error">{errors.dataEvento.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="dataInicioContrato">Data de Inicio do Contrato *</label>
              <input id="dataInicioContrato" type="date" {...register('dataInicioContrato')} />
              {errors.dataInicioContrato && (
                <span className="field-error">{errors.dataInicioContrato.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="valorAluguel">Valor do Aluguel (R$) *</label>
              <input
                id="valorAluguel"
                type="number"
                step="0.01"
                min={0}
                {...register('valorAluguel', { valueAsNumber: true })}
              />
              {errors.valorAluguel && (
                <span className="field-error">{errors.valorAluguel.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="diasVacancia">Dias de Vacancia *</label>
              <input
                id="diasVacancia"
                type="number"
                step="1"
                min={0}
                {...register('diasVacancia', { valueAsNumber: true })}
              />
              {errors.diasVacancia && (
                <span className="field-error">{errors.diasVacancia.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="mes">Mes *</label>
              <input
                id="mes"
                type="number"
                step="1"
                min={1}
                max={12}
                {...register('mes', { valueAsNumber: true })}
              />
              {errors.mes && <span className="field-error">{errors.mes.message}</span>}
            </div>

            <div className="field">
              <label htmlFor="ano">Ano *</label>
              <input
                id="ano"
                type="number"
                step="1"
                min={2000}
                {...register('ano', { valueAsNumber: true })}
              />
              {errors.ano && <span className="field-error">{errors.ano.message}</span>}
            </div>
          </div>

          <div className="field">
            <label htmlFor="motivoDesocupacao">Motivo da Desocupacao *</label>
            <textarea id="motivoDesocupacao" rows={3} {...register('motivoDesocupacao')} />
            {errors.motivoDesocupacao && (
              <span className="field-error">{errors.motivoDesocupacao.message}</span>
            )}
          </div>

          <div className="actions">
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar'}
            </button>
            <button type="button" className="btn-secondary" onClick={onExport}>
              Exportar {env.useMock ? '(CSV)' : 'XLSX'}
            </button>
          </div>
        </form>
      </div>

      <div className="section-title">
        <h2>Ultimos cadastros ({items.length})</h2>
      </div>

      <div className="card table-card">
        {items.length === 0 ? (
          <div className="empty">Nenhum registro ainda. Cadastre o primeiro acima.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Cidade</th>
                <th>Edificio</th>
                <th>Apto</th>
                <th>Area</th>
                <th>Tipologia</th>
                <th>Uso</th>
                <th>Status</th>
                <th>Data Evento</th>
                <th>Inicio Contrato</th>
                <th>Aluguel</th>
                <th>Dias Vac.</th>
                <th>Mes</th>
                <th>Ano</th>
                <th>Motivo</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {items.map((d) => {
                const isRemoving = removingIds.has(d.id);
                return (
                  <tr key={d.id}>
                    <td>{d.cidade}</td>
                    <td>{d.edificio}</td>
                    <td>{d.numeroApto}</td>
                    <td>{d.areaPrivativa.toFixed(2)}</td>
                    <td>{d.tipologia}</td>
                    <td>{d.uso}</td>
                    <td>{d.statusEvento}</td>
                    <td>{d.dataEvento}</td>
                    <td>{d.dataInicioContrato}</td>
                    <td>{d.valorAluguel.toFixed(2)}</td>
                    <td>{d.diasVacancia}</td>
                    <td>{d.mes}</td>
                    <td>{d.ano}</td>
                    <td title={d.motivoDesocupacao}>
                      {d.motivoDesocupacao.length > 50
                        ? `${d.motivoDesocupacao.slice(0, 50)}...`
                        : d.motivoDesocupacao}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn-danger"
                        onClick={() => onRemove(d)}
                        disabled={isRemoving}
                      >
                        {isRemoving ? 'Removendo...' : 'Remover'}
                      </button>
                    </td>
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

export default function CadastroPage() {
  return (
    <>
      <AppHeader title="Cadastro de Desocupacoes" />
      <CadastroContent />
    </>
  );
}
