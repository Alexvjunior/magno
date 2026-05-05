import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from './App';
import { mockAuth } from './services/auth.mock';
import { renderWithRouter } from './test/render';

describe('App routes', () => {
  it('renders login route directly', () => {
    renderWithRouter(<App />, ['/login']);

    expect(screen.getByRole('heading', { name: 'Entrar' })).toBeInTheDocument();
  });

  it('redirects unknown anonymous routes through the protected dashboard to login', async () => {
    renderWithRouter(<App />, ['/unknown']);

    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument();
  });

  it('renders protected dashboard for authenticated users', async () => {
    await mockAuth.login('user@example.com', 'password1');
    renderWithRouter(<App />, ['/dashboard']);

    expect(screen.getByTitle('Relatorio Data Studio')).toBeInTheDocument();
  });
});
