import { fireEvent, screen } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import AppHeader from './AppHeader';
import Modal from './Modal';
import ProtectedRoute from './ProtectedRoute';
import { mockAuth } from '../services/auth.mock';
import { renderWithRouter } from '../test/render';

describe('ProtectedRoute', () => {
  it('redirects anonymous users to login', () => {
    renderWithRouter(
      <Routes>
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <div>Dashboard privado</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>Pagina de login</div>} />
      </Routes>,
      ['/dashboard'],
    );

    expect(screen.getByText('Pagina de login')).toBeInTheDocument();
    expect(screen.queryByText('Dashboard privado')).not.toBeInTheDocument();
  });

  it('renders children for authenticated users', async () => {
    await mockAuth.login('user@example.com', 'password1');

    renderWithRouter(
      <ProtectedRoute>
        <div>Dashboard privado</div>
      </ProtectedRoute>,
    );

    expect(screen.getByText('Dashboard privado')).toBeInTheDocument();
  });
});

describe('Modal', () => {
  it('closes on escape and backdrop but not on inner clicks', () => {
    const onClose = vi.fn();
    renderWithRouter(
      <Modal title="Cadastro" onClose={onClose}>
        <button type="button">Dentro</button>
      </Modal>,
    );

    expect(screen.getByRole('dialog', { name: 'Cadastro' })).toBeInTheDocument();
    fireEvent.mouseDown(screen.getByRole('button', { name: 'Dentro' }));
    expect(onClose).not.toHaveBeenCalled();

    fireEvent.keyDown(window, { key: 'Escape' });
    fireEvent.mouseDown(screen.getByRole('presentation'));
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});

describe('AppHeader', () => {
  it('shows user, mock badge and cadastro menu callbacks', async () => {
    await mockAuth.login('user@example.com', 'password1');
    const onOpenCadastro = vi.fn();
    const onOpenCadastroImoveis = vi.fn();

    renderWithRouter(
      <AppHeader
        title="Alugueis Magno Group"
        onOpenCadastro={onOpenCadastro}
        onOpenCadastroImoveis={onOpenCadastroImoveis}
      />,
    );

    expect(screen.getByText('Alugueis Magno Group')).toBeInTheDocument();
    expect(screen.getByText('MOCK')).toBeInTheDocument();
    expect(screen.getByText('user@example.com')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Cadastros' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Movimentacoes' }));
    expect(onOpenCadastro).toHaveBeenCalledOnce();

    fireEvent.click(screen.getByRole('button', { name: 'Cadastros' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Imoveis' }));
    expect(onOpenCadastroImoveis).toHaveBeenCalledOnce();
  });

  it('logs out and navigates to login', async () => {
    await mockAuth.login('user@example.com', 'password1');

    renderWithRouter(
      <Routes>
        <Route path="/" element={<AppHeader title="Cadastro" />} />
        <Route path="/login" element={<div>Login destino</div>} />
      </Routes>,
      ['/'],
    );

    fireEvent.click(screen.getByRole('button', { name: 'Sair' }));

    expect(await screen.findByText('Login destino')).toBeInTheDocument();
    expect(mockAuth.getCurrentUser()).toBeNull();
  });
});
