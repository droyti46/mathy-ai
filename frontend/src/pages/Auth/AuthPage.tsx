import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import logoMathy from '@/assets/images/logo-mathy.png';
import mascotFace from '@/assets/images/mascot-face.png';
import TextInput from '@/components/TextInput';
import Button from '@/components/Button';
import { useAuthStore } from '@/lib/store/auth.store';
import { AnimatePresence, LayoutGroup, motion } from 'framer-motion';

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
    if (t === tab) return;
    setTab(t);
    sp.set('tab', t);
    setSp(sp, { replace: true });
    setErr(null);
    // Сбрасывать подтверждение при переключении
    setPass2('');
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
          <Link to="/"><img src={logoMathy} alt="Мати" className="h-7" /></Link>
          <br></br>
          <div className="opacity-95 mb-6">Начни прокачивать свой математический скилл прямо сейчас</div>

          {/* Tabs */}
          <LayoutGroup>
            <div className="relative inline-flex p-1 rounded-full bg-white/90 backdrop-blur w-fit mb-6">
              {(['register','login'] as const).map((t) => {
                const active = tab === t;
                return (
                  <button
                    key={t}
                    onClick={() => switchTab(t)}
                    className={[
                      'relative px-6 py-2 rounded-full font-semibold',
                      'transition-colors duration-300',
                      active ? 'text-white' : 'text-primary-900'
                    ].join(' ')}
                    aria-pressed={active}
                  >
                    {/* Скользящая плашка-индикатор (shared layout) */}
                    {active && (
                      <motion.span
                        layoutId="tab-pill"
                        className="absolute inset-0 rounded-full bg-primary-500"
                        transition={{ type: 'spring', stiffness: 500, damping: 40, mass: 0.6 }}
                      />
                    )}
                    <span className="relative z-10">
                      {t === 'register' ? 'Регистрация' : 'Вход'}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Форма: плавная смена контента по табу */}
            <div className="relative">
              <AnimatePresence mode="wait" initial={false}>
                <motion.form
                  key={tab} // ключ меняется — AnimatePresence анимирует уход/приход
                  className="space-y-5"
                  onSubmit={onSubmit}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
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

                  {/* Плавное появление подтверждения пароля */}
                  <AnimatePresence initial={false}>
                    {tab === 'register' && (
                      <motion.div
                        key="confirm"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        className="overflow-hidden"
                      >
                        <TextInput
                          type="password"
                          placeholder="Повторите ваш пароль"
                          value={pass2}
                          onChange={(e) => setPass2(e.target.value)}
                          required
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {err && <div className="text-red-200">{err}</div>}

                  <Button
                    type="submit"
                    disabled={loading}
                    className="!bg-white !text-primary-900 hover:!bg-primary-200 transition-colors"
                  >
                    {loading ? 'Загрузка...' : (tab==='register' ? 'Зарегистрироваться' : 'Войти')}
                  </Button>
                </motion.form>
              </AnimatePresence>
            </div>
          </LayoutGroup>
        </div>
      </div>

      {/* RIGHT: mascot */}
      <div className="bg-white flex items-center justify-center">
        <img src={mascotFace} alt="" className="w-72 md:w-[420px] object-contain" />
      </div>
    </div>
  );
}
