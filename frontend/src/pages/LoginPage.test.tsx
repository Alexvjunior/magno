import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import LoginPage from './LoginPage';
import { renderWithRouter } from '../test/render';

const authServiceMock = vi.hoisted(() => ({
  login: vi.fn(),
  completeNewPassword: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn(),
}));

vi.mock('../services/auth', () => ({
  authService: authServiceMock,
}));

function renderLogin() {
  return renderWithRouter(
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<div>Dashboard destino</div>} />
    </Routes>,
    ['/login'],
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    authServiceMock.login.mockReset();
    authServiceMock.completeNewPassword.mockReset();
    authServiceMock.logout.mockReset();
    authServiceMock.getCurrentUser.mockReset();
  });

  it('validates login form before submit', async () => {
    const user = userEvent.setup();
    renderLogin();

    await user.type(screen.getByLabelText('E-mail'), 'email-invalido');
    await user.type(screen.getByLabelText('Senha'), 'short');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(await screen.findByText('E-mail inválido')).toBeInTheDocument();
    expect(await screen.findByText(/8 caracteres/)).toBeInTheDocument();
    expect(authServiceMock.login).not.toHaveBeenCalled();
  });

  it('navigates to dashboard after successful login', async () => {
    const user = userEvent.setup();
    authServiceMock.login.mockResolvedValue({
      kind: 'success',
      user: { sub: 'user-1', email: 'user@example.com', token: 'token' },
    });
    renderLogin();

    await user.type(screen.getByLabelText('E-mail'), 'user@example.com');
    await user.type(screen.getByLabelText('Senha'), 'password1');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(await screen.findByText('Dashboard destino')).toBeInTheDocument();
    expect(authServiceMock.login).toHaveBeenCalledWith('user@example.com', 'password1');
  });

  it('shows server login errors', async () => {
    const user = userEvent.setup();
    authServiceMock.login.mockRejectedValue(new Error('Credenciais invalidas'));
    renderLogin();

    await user.type(screen.getByLabelText('E-mail'), 'user@example.com');
    await user.type(screen.getByLabelText('Senha'), 'password1');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(await screen.findByText('Credenciais invalidas')).toBeInTheDocument();
  });

  it('handles new password challenge, validation and back action', async () => {
    const user = userEvent.setup();
    authServiceMock.login.mockResolvedValue({ kind: 'newPasswordRequired' });
    authServiceMock.completeNewPassword.mockResolvedValue({
      sub: 'user-1',
      email: 'user@example.com',
      token: 'token',
    });
    renderLogin();

    await user.type(screen.getByLabelText('E-mail'), 'user@example.com');
    await user.type(screen.getByLabelText('Senha'), 'password1');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(await screen.findByRole('heading', { name: 'Definir nova senha' })).toBeInTheDocument();
    await user.type(screen.getByLabelText('Nova senha'), 'password');
    await user.type(screen.getByLabelText('Confirmar nova senha'), 'different');
    await user.click(screen.getByRole('button', { name: 'Salvar senha' }));
    expect(await screen.findAllByText(/maiuscula|iguais/)).toHaveLength(2);
    expect(authServiceMock.completeNewPassword).not.toHaveBeenCalled();

    await user.clear(screen.getByLabelText('Nova senha'));
    await user.clear(screen.getByLabelText('Confirmar nova senha'));
    await user.type(screen.getByLabelText('Nova senha'), 'Password1');
    await user.type(screen.getByLabelText('Confirmar nova senha'), 'Password1');
    await user.click(screen.getByRole('button', { name: 'Salvar senha' }));
    expect(await screen.findByText('Dashboard destino')).toBeInTheDocument();
  });

  it('returns to login and clears transient errors from new password step', async () => {
    const user = userEvent.setup();
    authServiceMock.login.mockResolvedValue({ kind: 'newPasswordRequired' });
    renderLogin();

    await user.type(screen.getByLabelText('E-mail'), 'user@example.com');
    await user.type(screen.getByLabelText('Senha'), 'password1');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));
    await screen.findByRole('heading', { name: 'Definir nova senha' });
    await user.click(screen.getByRole('button', { name: 'Voltar' }));

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Entrar' })).toBeInTheDocument());
    expect(screen.getByLabelText('Senha')).toHaveValue('');
  });
});
