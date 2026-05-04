import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';
import {
  loginSchema,
  newPasswordSchema,
  type LoginForm,
  type NewPasswordForm,
} from '../services/schemas';
import { env } from '../config/env';

type LoginStep = 'login' | 'newPassword';

export default function LoginPage() {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [step, setStep] = useState<LoginStep>('login');
  const {
    register: registerLogin,
    handleSubmit: handleLoginSubmit,
    setValue: setLoginValue,
    formState: { errors: loginErrors, isSubmitting: isLoginSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });
  const {
    register: registerNewPassword,
    handleSubmit: handleNewPasswordSubmit,
    reset: resetNewPassword,
    formState: { errors: newPasswordErrors, isSubmitting: isSettingPassword },
  } = useForm<NewPasswordForm>({
    resolver: zodResolver(newPasswordSchema),
    defaultValues: { newPassword: '', confirmPassword: '' },
  });

  async function onLoginSubmit(values: LoginForm) {
    setServerError(null);
    try {
      const result = await authService.login(values.email, values.password);
      if (result.kind === 'newPasswordRequired') {
        resetNewPassword({ newPassword: '', confirmPassword: '' });
        setStep('newPassword');
        return;
      }
      navigate('/dashboard', { replace: true });
    } catch (e) {
      setServerError(e instanceof Error ? e.message : 'Erro ao entrar');
    }
  }

  async function onNewPasswordSubmit(values: NewPasswordForm) {
    setServerError(null);
    try {
      await authService.completeNewPassword(values.newPassword);
      navigate('/dashboard', { replace: true });
    } catch (e) {
      setServerError(e instanceof Error ? e.message : 'Erro ao definir nova senha');
    }
  }

  function backToLogin() {
    setServerError(null);
    setLoginValue('password', '');
    resetNewPassword({ newPassword: '', confirmPassword: '' });
    setStep('login');
  }

  return (
    <div className="center-screen">
      <div className="card card-narrow">
        <h1>{step === 'login' ? 'Entrar' : 'Definir nova senha'}</h1>
        <p className="muted">
          {step === 'newPassword'
            ? 'Defina uma senha permanente para concluir o primeiro acesso.'
            : env.useMock
              ? 'Modo mock: qualquer e-mail e senha com 8 ou mais caracteres entra.'
              : 'Use suas credenciais do Cognito.'}
        </p>

        {serverError && <div className="alert alert-error">{serverError}</div>}

        {step === 'login' ? (
          <form onSubmit={handleLoginSubmit(onLoginSubmit)} noValidate>
            <div className="field">
              <label htmlFor="email">E-mail</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                {...registerLogin('email')}
                aria-invalid={!!loginErrors.email}
              />
              {loginErrors.email && <span className="field-error">{loginErrors.email.message}</span>}
            </div>

            <div className="field">
              <label htmlFor="password">Senha</label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                {...registerLogin('password')}
                aria-invalid={!!loginErrors.password}
              />
              {loginErrors.password && <span className="field-error">{loginErrors.password.message}</span>}
            </div>

            <button type="submit" className="btn-primary" disabled={isLoginSubmitting} style={{ width: '100%' }}>
              {isLoginSubmitting ? 'Entrando...' : 'Entrar'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleNewPasswordSubmit(onNewPasswordSubmit)} noValidate>
            <div className="field">
              <label htmlFor="newPassword">Nova senha</label>
              <input
                id="newPassword"
                type="password"
                autoComplete="new-password"
                {...registerNewPassword('newPassword')}
                aria-invalid={!!newPasswordErrors.newPassword}
              />
              {newPasswordErrors.newPassword && (
                <span className="field-error">{newPasswordErrors.newPassword.message}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="confirmPassword">Confirmar nova senha</label>
              <input
                id="confirmPassword"
                type="password"
                autoComplete="new-password"
                {...registerNewPassword('confirmPassword')}
                aria-invalid={!!newPasswordErrors.confirmPassword}
              />
              {newPasswordErrors.confirmPassword && (
                <span className="field-error">{newPasswordErrors.confirmPassword.message}</span>
              )}
            </div>

            <div className="actions">
              <button type="submit" className="btn-primary" disabled={isSettingPassword} style={{ flex: 1 }}>
                {isSettingPassword ? 'Salvando...' : 'Salvar senha'}
              </button>
              <button type="button" className="btn-secondary" onClick={backToLogin} disabled={isSettingPassword}>
                Voltar
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
