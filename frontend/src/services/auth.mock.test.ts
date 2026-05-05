import { describe, expect, it } from 'vitest';
import { mockAuth } from './auth.mock';

describe('mockAuth', () => {
  it('persists login user and clears it on logout', async () => {
    const result = await mockAuth.login('user@example.com', 'password1');

    expect(result.kind).toBe('success');
    expect(mockAuth.getCurrentUser()?.email).toBe('user@example.com');

    await mockAuth.logout();
    expect(mockAuth.getCurrentUser()).toBeNull();
  });

  it('rejects missing credentials and short passwords', async () => {
    await expect(mockAuth.login('', 'password1')).rejects.toThrow('Informe e-mail e senha');
    await expect(mockAuth.login('user@example.com', 'short')).rejects.toThrow(
      'Senha precisa ter pelo menos 8 caracteres',
    );
  });

  it('does not support new password challenge in mock mode', async () => {
    await expect(mockAuth.completeNewPassword('short')).rejects.toThrow(
      'Senha precisa ter pelo menos 8 caracteres',
    );
    await expect(mockAuth.completeNewPassword('Password1')).rejects.toThrow(
      'Nenhum desafio de nova senha pendente.',
    );
  });
});

