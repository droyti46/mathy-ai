import { NavLink, Outlet } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from '@/lib/store/auth.store';
import { api } from '@/lib/api/axios';
import ducklar from '@/assets/images/ducklar.png';

export default function MainPage() {
  const { user, setUser } = useAuthStore();

  useEffect(() => {
    // получаем ник после логина/регистрации
    const load = async () => {
      try {
        const { data } = await api.get('/api/auth/me'); // UserOut  :contentReference[oaicite:1]{index=1}
        setUser(data);
      } catch {}
    };
    if (!user) load();
  }, [user, setUser]);

  return (
    <div className="min-h-screen bg-primary-500/90">
      <header className="bg-primary-500 text-white">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="text-4xl font-extrabold">Мати</div>
          <nav className="flex gap-8 text-2xl">
            <Tab to="/app/theory">Теория</Tab>
            <Tab to="/app/tasks">Задачи</Tab>
            <Tab to="/app/daily">Ежедневная задача</Tab>
          </nav>
          <div className="flex items-center gap-3 text-lg">
            <img src={ducklar} alt="" className="w-6 h-6" />
            <span className="opacity-95">5</span>{/* заглушка количества дакларов */}
            <span className="opacity-90">{user?.login ?? 'user'}</span>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}

function Tab({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        'pb-1 border-b-2 transition ' +
        (isActive ? 'border-white' : 'border-transparent opacity-80 hover:opacity-100')
      }
    >
      {children}
    </NavLink>
  );
}
