import { Navigate } from 'react-router-dom';
import { authService } from '../services/auth';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const user = authService.getCurrentUser();
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
