import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { env } from '../config/env';
import { authService } from '../services/auth';

type AppHeaderProps = {
  title: string;
  onOpenCadastro?: () => void;
  onOpenCadastroImoveis?: () => void;
};

export default function AppHeader({ title, onOpenCadastro, onOpenCadastroImoveis }: AppHeaderProps) {
  const navigate = useNavigate();
  const user = authService.getCurrentUser();
  const [isCadastroMenuOpen, setIsCadastroMenuOpen] = useState(false);
  const showCadastroMenu = Boolean(onOpenCadastro || onOpenCadastroImoveis);

  async function onLogout() {
    await authService.logout();
    navigate('/login', { replace: true });
  }

  function openCadastro() {
    setIsCadastroMenuOpen(false);
    onOpenCadastro?.();
  }

  function openCadastroImoveis() {
    setIsCadastroMenuOpen(false);
    onOpenCadastroImoveis?.();
  }

  return (
    <header className="app-header">
      <div className="brand">{title}</div>
      <div className="user">
        {env.useMock && <span className="badge">MOCK</span>}
        <span className="user-email">{user?.email}</span>
        {showCadastroMenu && (
          <div className="dropdown">
            <button
              type="button"
              className="btn-secondary dropdown-trigger"
              onClick={() => setIsCadastroMenuOpen((value) => !value)}
              aria-expanded={isCadastroMenuOpen}
              aria-haspopup="menu"
            >
              Cadastros
            </button>
            {isCadastroMenuOpen && (
              <div className="dropdown-menu" role="menu">
                {onOpenCadastro && (
                  <button type="button" role="menuitem" onClick={openCadastro}>
                    Movimentacoes
                  </button>
                )}
                {onOpenCadastroImoveis && (
                  <button type="button" role="menuitem" onClick={openCadastroImoveis}>
                    Imoveis
                  </button>
                )}
              </div>
            )}
          </div>
        )}
        <button className="btn-secondary" onClick={onLogout}>
          Sair
        </button>
      </div>
    </header>
  );
}
