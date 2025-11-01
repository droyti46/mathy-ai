import { createBrowserRouter, Navigate } from 'react-router-dom';
import WelcomePage from '@/pages/Welcome/WelcomePage';
import AuthPage from '@/pages/Auth/AuthPage';
import MainPage from '@/pages/Main/MainPage';
import ProtectedRoute from './ProtectedRoute';

export const router = createBrowserRouter([
  { path: '/', element: <WelcomePage /> },
  { path: '/auth', element: <AuthPage /> },
  {
    path: '/app',
    element: (
      <ProtectedRoute>
        <MainPage />
      </ProtectedRoute>
    ),
  },
  { path: '*', element: <Navigate to="/" replace /> }
]);
