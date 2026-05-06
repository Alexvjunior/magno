import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import DashboardPage from './DashboardPage';
import { mockAuth } from '../services/auth.mock';
import { renderWithRouter } from '../test/render';

vi.mock('./CadastroPage', () => ({
  CadastroContent: () => <div>Formulario movimentacoes</div>,
}));

vi.mock('./CadastroImoveisPage', () => ({
  CadastroImoveisContent: () => <div>Formulario imoveis</div>,
}));

describe('DashboardPage', () => {
  it('renders the Data Studio iframe and opens/closes cadastro modals', async () => {
    const user = userEvent.setup();
    await mockAuth.login('user@example.com', 'password1');
    renderWithRouter(<DashboardPage />);

    const frame = screen.getByTitle('Relatorio Data Studio');
    expect(frame).toHaveAttribute(
      'src',
      'https://datastudio.google.com/embed/reporting/4b948a58-2496-4c8c-a2cb-7970823a2e63/page/N4agF',
    );

    await user.click(screen.getByRole('button', { name: 'Cadastros' }));
    await user.click(screen.getByRole('menuitem', { name: 'Movimentacoes' }));
    expect(screen.getByRole('dialog', { name: 'Cadastro de movimentacoes' })).toBeInTheDocument();
    expect(screen.getByText('Formulario movimentacoes')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Fechar' }));

    await user.click(screen.getByRole('button', { name: 'Cadastros' }));
    await user.click(screen.getByRole('menuitem', { name: 'Imoveis' }));
    expect(screen.getByRole('dialog', { name: 'Cadastro de imoveis' })).toBeInTheDocument();
    expect(screen.getByText('Formulario imoveis')).toBeInTheDocument();
  });
});
