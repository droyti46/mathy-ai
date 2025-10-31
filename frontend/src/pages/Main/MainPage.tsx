import { useAuthStore } from '@/lib/store/auth.store';

export default function MainPage() {
  const { logout } = useAuthStore();
  return (
    <div className="min-h-screen flex flex-col items-center justify-center">
      <div className="text-3xl font-bold mb-3">Главный экран (заглушка)</div>
      <div className="opacity-70 mb-6">Здесь позже будут вкладки: Теория / Задачи / Ежедневная</div>
      <button
        onClick={logout}
        className="rounded-xl2 px-6 py-3 border-2 border-primary-500 text-primary-900 hover:bg-primary-200"
      >
        Выйти
      </button>
    </div>
  );
}
