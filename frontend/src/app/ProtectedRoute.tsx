import { ReactNode, useEffect } from 'react';
import { useAuthStore } from '@/lib/store/auth.store';
import { Navigate } from 'react-router-dom';

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { accessToken, hydrate } = useAuthStore();

  useEffect(() => { hydrate(); }, [hydrate]);

  if (!accessToken) {
    return <Navigate to="/auth" replace />;
  }
  return <>{children}</>;
}
