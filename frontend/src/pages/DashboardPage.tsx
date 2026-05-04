import { useState } from 'react';
import AppHeader from '../components/AppHeader';
import Modal from '../components/Modal';
import { CadastroContent } from './CadastroPage';

const dashboards = [
  {
    label: 'Aba 1',
    title: 'Dashboard Aba 1',
    url: 'https://lookerstudio.google.com/embed/reporting/4b948a58-2496-4c8c-a2cb-7970823a2e63/page/N4agF',
  },
  {
    label: 'Aba 2',
    title: 'Dashboard Aba 2',
    url: 'https://lookerstudio.google.com/embed/reporting/4b948a58-2496-4c8c-a2cb-7970823a2e63/page/p_4szz1urfyd',
  },
];

export default function DashboardPage() {
  const [activeDashboard, setActiveDashboard] = useState(0);
  const [isCadastroOpen, setIsCadastroOpen] = useState(false);
  const dashboard = dashboards[activeDashboard];

  return (
    <div className="dashboard-shell">
      <AppHeader title="Alugueis Magno Group" onOpenCadastro={() => setIsCadastroOpen(true)} />

      <main className="dashboard-main">
        <div className="dashboard-tabs" role="tablist" aria-label="Dashboards">
          {dashboards.map((item, index) => (
            <button
              key={item.url}
              type="button"
              role="tab"
              className={index === activeDashboard ? 'tab-button active' : 'tab-button'}
              aria-selected={index === activeDashboard}
              onClick={() => setActiveDashboard(index)}
            >
              {item.label}
            </button>
          ))}
        </div>

        <section className="dashboard-frame-panel">
          <iframe
            key={dashboard.url}
            title={dashboard.title}
            src={dashboard.url}
            className="dashboard-frame"
            loading="lazy"
            allowFullScreen
          />
        </section>
      </main>

      {isCadastroOpen && (
        <Modal title="Cadastro de desocupacoes" onClose={() => setIsCadastroOpen(false)}>
          <CadastroContent embedded />
        </Modal>
      )}
    </div>
  );
}
