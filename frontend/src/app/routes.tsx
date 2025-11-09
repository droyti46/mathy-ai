import { createBrowserRouter, Navigate } from 'react-router-dom';
import WelcomePage from '@/pages/Welcome/WelcomePage';
import AuthPage from '@/pages/Auth/AuthPage';
import MainPage from '@/pages/Main/MainPage';
import TheoryLessonPage from '@/pages/Main/TheoryLessonPage';
import ProtectedRoute from './ProtectedRoute';

// новые вкладки и страница-заглушка задачи
import TasksTab from '@/pages/Main/TasksTab';
import TheoryTab from '@/pages/Main/TheoryTab';
import DailyTab from '@/pages/Main/DailyTab';
import TaskPage from '@/pages/Task/TaskPage';

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
    children: [
      { index: true, element: <Navigate to="tasks" replace /> },
      { path: 'theory/:themeId/:lessonId', element: <TheoryLessonPage /> },
      { path: 'theory', element: <TheoryTab /> },
      { path: 'tasks', element: <TasksTab /> },     // вкладка по умолчанию
      { path: 'daily', element: <DailyTab /> },
    ],
  },
  { path: '/task/:taskId', element: (
      <ProtectedRoute>
        <TaskPage />
      </ProtectedRoute>
    )
  },
  { path: '*', element: <Navigate to="/" replace /> }
]);
