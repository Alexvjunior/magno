import {
  AuthenticationDetails,
  CognitoUser,
  CognitoUserPool,
  CognitoUserSession,
  type ICognitoUserData,
} from 'amazon-cognito-identity-js';
import { env } from '../config/env';
import type { AuthUser } from '../types';
import { mockAuth } from './auth.mock';

export type LoginResult =
  | { kind: 'success'; user: AuthUser }
  | { kind: 'newPasswordRequired' };

export interface AuthService {
  login(email: string, password: string): Promise<LoginResult>;
  completeNewPassword(newPassword: string): Promise<AuthUser>;
  logout(): Promise<void>;
  getCurrentUser(): AuthUser | null;
}

class CognitoAuth implements AuthService {
  private readonly pool: CognitoUserPool;
  private pendingUser: CognitoUser | null = null;

  constructor(userPoolId: string, clientId: string) {
    this.pool = new CognitoUserPool({ UserPoolId: userPoolId, ClientId: clientId });
  }

  login(email: string, password: string): Promise<LoginResult> {
    const userData: ICognitoUserData = { Username: email, Pool: this.pool };
    const cognitoUser = new CognitoUser(userData);
    const authDetails = new AuthenticationDetails({ Username: email, Password: password });

    return new Promise<LoginResult>((resolve, reject) => {
      cognitoUser.authenticateUser(authDetails, {
        onSuccess: (session) => {
          this.pendingUser = null;
          resolve({ kind: 'success', user: toAuthUser(session, email) });
        },
        onFailure: (err) => {
          this.pendingUser = null;
          reject(toError(err));
        },
        newPasswordRequired: () => {
          this.pendingUser = cognitoUser;
          resolve({ kind: 'newPasswordRequired' });
        },
      });
    });
  }

  completeNewPassword(newPassword: string): Promise<AuthUser> {
    const cognitoUser = this.pendingUser;
    if (!cognitoUser) {
      return Promise.reject(new Error('Nenhum desafio de nova senha pendente.'));
    }
    return new Promise<AuthUser>((resolve, reject) => {
      cognitoUser.completeNewPasswordChallenge(
        newPassword,
        {},
        {
          onSuccess: (session) => {
            this.pendingUser = null;
            resolve(toAuthUser(session, cognitoUser.getUsername()));
          },
          onFailure: (err) => {
            reject(toError(err));
          },
        },
      );
    });
  }

  logout(): Promise<void> {
    const current = this.pool.getCurrentUser();
    if (current) current.signOut();
    this.pendingUser = null;
    return Promise.resolve();
  }

  getCurrentUser(): AuthUser | null {
    const cognitoUser = this.pool.getCurrentUser();
    if (!cognitoUser) return null;

    let cached: AuthUser | null = null;
    cognitoUser.getSession((err: Error | null, session: CognitoUserSession | null) => {
      if (err || !session || !session.isValid()) return;
      cached = toAuthUser(session, cognitoUser.getUsername());
    });
    return cached;
  }
}

function toAuthUser(session: CognitoUserSession, fallbackEmail: string): AuthUser {
  const idToken = session.getIdToken();
  const payload = idToken.decodePayload() as Record<string, unknown>;
  return {
    sub: String(payload.sub ?? ''),
    email: String(payload.email ?? fallbackEmail),
    name: typeof payload.name === 'string' ? payload.name : undefined,
    token: idToken.getJwtToken(),
  };
}

function toError(err: unknown): Error {
  if (err instanceof Error) return err;
  if (typeof err === 'object' && err !== null && 'message' in err) {
    return new Error(String((err as { message: unknown }).message));
  }
  return new Error('Falha ao autenticar');
}

function buildService(): AuthService {
  if (env.useMock) return mockAuth;
  if (!env.userPoolId || !env.userPoolClientId) {
    throw new Error(
      'Cognito não configurado. Defina VITE_USER_POOL_ID e VITE_USER_POOL_CLIENT_ID, ou VITE_USE_MOCK=true.',
    );
  }
  return new CognitoAuth(env.userPoolId, env.userPoolClientId);
}

export const authService: AuthService = buildService();
