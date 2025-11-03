import { Link, NavLink, Outlet } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/store/auth.store';
import { api } from '@/lib/api/axios';
import ducklar from '@/assets/images/ducklar.png';
import logoMathy from '@/assets/images/logo-mathy.png';

export default function MainPage() {
  const { user, setUser } = useAuthStore();
  const [coins, setCoins] = useState<number>(0);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        // 1) сначала получаем пользователя
        const me = await api.get('/api/auth/me');
        if (cancelled) return;
        setUser(me.data);

        // 2) затем — статы (к этому моменту всё уже инициализировано)
        const stats = await api.get('/api/auth/me/stats');
        if (cancelled) return;
        setCoins(stats.data?.coins ?? 0);
      } catch {
        // можно оставить 0
      }
    })();

    return () => { cancelled = true; };
  }, [setUser]); // зависит только от setUser, чтобы эффект не дергался лишний раз

  return (
    <div className="min-h-screen bg-primary-500/90">
      <header className="bg-primary-500 text-white">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/"><img src={logoMathy} alt="Мати" className="h-7" /></Link>

          <nav className="flex gap-8 text-[20px]">
            <Tab to="/app/theory">Теория</Tab>
            <Tab to="/app/tasks">Задачи</Tab>
            <Tab to="/app/daily">Ежедневная задача</Tab>
          </nav>

          <div className="flex items-center gap-3 text-lg">
            <span className="opacity-95">{coins}</span> {/* ← тут показываем монетки */}
            <img src={ducklar} alt="" className="w-[40px]" />
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
