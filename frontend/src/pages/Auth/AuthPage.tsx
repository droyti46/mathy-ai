import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import mascotFace from '@/assets/images/mascot-face.png';
import TextInput from '@/components/TextInput';
import Button from '@/components/Button';
import { useAuthStore } from '@/lib/store/auth.store';

export default function AuthPage() {
  const [sp, setSp] = useSearchParams();
  const initialTab = useMemo(() => (sp.get('tab') === 'login' ? 'login' : 'register'), [sp]);
  const [tab, setTab] = useState<'register'|'login'>(initialTab as any);
  const nav = useNavigate();

  const { registerAndLogin, login, accessToken, hydrate } = useAuthStore();

  useEffect(() => { hydrate(); }, [hydrate]);
  useEffect(() => { if (accessToken) nav('/app', { replace: true }); }, [accessToken, nav]);

  const [loginVal, setLoginVal] = useState('');
  const [pass1, setPass1] = useState('');
  const [pass2, setPass2] = useState('');
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const switchTab = (t: 'register'|'login') => {
    setTab(t);
    sp.set('tab', t);
    setSp(sp, { replace: true });
    setErr(null);
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      if (tab === 'register') {
        if (pass1 !== pass2) { setErr('Пароли не совпадают'); return; }
        await registerAndLogin(loginVal.trim(), pass1);
      } else {
        await login(loginVal.trim(), pass1);
      }
    } catch (error: any) {
      setErr(error?.response?.data?.detail ?? 'Ошибка. Проверьте данные.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid md:grid-cols-2">
      {/* LEFT: form */}
      <div className="bg-primary-500 text-white flex flex-col justify-center">
        <div className="max-w-xl w-full mx-auto px-10">
          <div className="text-6xl font-extrabold mb-4">Мати</div>
          <div className="opacity-95 mb-6">Начни прокачивать свой математический скилл прямо сейчас</div>

          {/* Tabs */}
          <div className="flex bg-white rounded-full p-1 w-fit mb-6">
            <button
              onClick={() => switchTab('register')}
              className={`px-6 py-2 rounded-full font-semibold ${tab==='register' ? 'bg-primary-500 text-white' : 'text-primary-900'}`}
            >
              Регистрация
            </button>
            <button
              onClick={() => switchTab('login')}
              className={`px-6 py-2 rounded-full font-semibold ${tab==='login' ? 'bg-primary-500 text-white' : 'text-primary-900'}`}
            >
              Вход
            </button>
          </div>

          <form className="space-y-5" onSubmit={onSubmit}>
            <div>
              <label className="block mb-2">Логин</label>
              <TextInput
                placeholder="Придумайте логин"
                value={loginVal}
                onChange={(e) => setLoginVal(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block mb-2">Пароль</label>
              <TextInput
                type="password"
                placeholder={tab==='register' ? 'Придумайте пароль' : 'Введите пароль'}
                value={pass1}
                onChange={(e) => setPass1(e.target.value)}
                required
              />
            </div>
            {tab==='register' && (
              <div>
                <TextInput
                  type="password"
                  placeholder="Повторите ваш пароль"
                  value={pass2}
                  onChange={(e) => setPass2(e.target.value)}
                  required
                />
              </div>
            )}
            {err && <div className="text-red-200">{err}</div>}
            <Button type="submit" disabled={loading} className="!bg-white !text-primary-900 hover:!bg-primary-200">
              {loading ? 'Загрузка...' : (tab==='register' ? 'Зарегистрироваться' : 'Войти')}
            </Button>
          </form>
        </div>
      </div>

      {/* RIGHT: mascot */}
      <div className="bg-white flex items-center justify-center">
        <img src={mascotFace} alt="" className="w-72 md:w-[420px] object-contain" />
      </div>
    </div>
  );
}
