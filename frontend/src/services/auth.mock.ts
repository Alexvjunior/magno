import type { AuthUser } from '../types';
import type { AuthService, LoginResult } from './auth';

const STORAGE_KEY = 'claud.mock.user';

function fakeToken(): string {
  return 'mock.' + Math.random().toString(36).slice(2) + '.' + Date.now();
}

export const mockAuth: AuthService = {
  async login(email: string, password: string): Promise<LoginResult> {
    if (!email || !password) throw new Error('Informe e-mail e senha');
    if (password.length < 8) throw new Error('Senha precisa ter pelo menos 8 caracteres');
    const user: AuthUser = {
      sub: 'mock-' + email,
      email,
      name: email.split('@')[0],
      token: fakeToken(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    return { kind: 'success', user };
  },
  async completeNewPassword(newPassword: string): Promise<AuthUser> {
    if (newPassword.length < 8) throw new Error('Senha precisa ter pelo menos 8 caracteres');
    throw new Error('Nenhum desafio de nova senha pendente.');
  },
  async logout() {
    localStorage.removeItem(STORAGE_KEY);
  },
  getCurrentUser(): AuthUser | null {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  },
};
