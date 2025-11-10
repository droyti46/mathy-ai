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

import AboutPage from "@/pages/Static/AboutPage";
import AboutMatyPage from "@/pages/Static/AboutMatyPage";
import TeamPage from "@/pages/Static/TeamPage";
import TermsPage from "@/pages/Static/TermsPage";
import PrivacyPage from "@/pages/Static/PrivacyPage";

export const router = createBrowserRouter([
  { path: '/', element: <WelcomePage /> },
  { path: '/auth', element: <AuthPage /> },
  { path: "/about", element: <AboutPage /> },
  { path: "/about/maty", element: <AboutMatyPage /> },
  { path: "/about/team", element: <TeamPage /> },
  { path: "/terms", element: <TermsPage /> },
  { path: "/privacy", element: <PrivacyPage /> },
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
