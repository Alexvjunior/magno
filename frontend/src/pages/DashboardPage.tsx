import { useState } from 'react';
import AppHeader from '../components/AppHeader';
import Modal from '../components/Modal';
import { CadastroContent } from './CadastroPage';
import { CadastroImoveisContent } from './CadastroImoveisPage';

const DATA_STUDIO_REPORT_URL =
  'https://datastudio.google.com/embed/reporting/4b948a58-2496-4c8c-a2cb-7970823a2e63/page/N4agF';

export default function DashboardPage() {
  const [activeCadastro, setActiveCadastro] = useState<'movimentacoes' | 'imoveis' | null>(null);

  return (
    <div className="dashboard-shell">
      <AppHeader
        title="Alugueis Magno Group"
        onOpenCadastro={() => setActiveCadastro('movimentacoes')}
        onOpenCadastroImoveis={() => setActiveCadastro('imoveis')}
      />

      <main className="dashboard-main">
        <section className="dashboard-frame-panel">
          <iframe
            title="Relatorio Data Studio"
            src={DATA_STUDIO_REPORT_URL}
            className="dashboard-frame"
            loading="lazy"
            allowFullScreen
            sandbox="allow-storage-access-by-user-activation allow-scripts allow-same-origin allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox allow-downloads"
          />
        </section>
      </main>

      {activeCadastro && (
        <Modal
          title={activeCadastro === 'imoveis' ? 'Cadastro de imoveis' : 'Cadastro de movimentacoes'}
          onClose={() => setActiveCadastro(null)}
        >
          {activeCadastro === 'imoveis' ? <CadastroImoveisContent embedded /> : <CadastroContent embedded />}
        </Modal>
      )}
    </div>
  );
}
