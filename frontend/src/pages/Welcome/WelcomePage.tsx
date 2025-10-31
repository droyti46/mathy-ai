import { Link, useNavigate } from 'react-router-dom';
import CloudField from '@/components/CloudField';
import sun from '@/assets/images/sun-top-right.png';
import cloud1 from '@/assets/images/cloud-1.png';
import cloud2 from '@/assets/images/cloud-2.png';
import cloud3 from '@/assets/images/cloud-3.png';
import mascotHead from '@/assets/images/mascot-head.png';
import shapesRow from '@/assets/images/shapes-row.png';
import logoSber from '@/assets/images/logo-sber.png';
import logoCU from '@/assets/images/logo-central-university.png';

import icon1 from '@/assets/images/icon-math-analysis.png';
import icon2 from '@/assets/images/icon-linear-geometry.png';
import icon3 from '@/assets/images/icon-probability-stat.png';
import icon4 from '@/assets/images/icon-discrete-math.png';
import icon5 from '@/assets/images/icon-differential-eq.png';
import icon6 from '@/assets/images/icon-numerical.png';
import icon7 from '@/assets/images/icon-optimization.png';
import icon8 from '@/assets/images/icon-number-theory.png';
import icon9 from '@/assets/images/icon-functional-analysis.png';
import icon10 from '@/assets/images/icon-applied-math.png';
import Button from '@/components/Button';

export default function WelcomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      {/* HERO */}
      <header className="relative bg-primary-500 text-white overflow-hidden">
        <img src={sun} alt="" className="pointer-events-none select-none absolute right-0 top-0 w-48 md:w-64" />
        <CloudField sprites={[cloud1, cloud2, cloud3]} density={4} />
        <div className="container mx-auto px-6 py-6 flex justify-between items-center">
          <div className="text-2xl font-semibold">Мати</div>
          <nav className="space-x-8 text-lg">
            <Link to="/auth?tab=register" className="opacity-90 hover:opacity-100">Регистрация</Link>
            <Link to="/auth?tab=login" className="opacity-90 hover:opacity-100">Вход</Link>
          </nav>
        </div>
        <div className="container mx-auto px-6 py-16 md:py-24 text-center">
          <h1 className="text-4xl md:text-6xl font-extrabold">Математический тренажёр</h1>
          <p className="mt-6 opacity-90">Решение математических задач с автоматической проверкой от ИИ</p>
          <div className="mt-8">
            <Button onClick={() => navigate('/auth?tab=register')}>Попробовать</Button>
          </div>
        </div>
      </header>

      {/* ICONS GRID */}
      <section className="container mx-auto px-6 py-10">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-8 text-center">
          {[icon1,icon2,icon3,icon4,icon5,icon6,icon7,icon8,icon9,icon10].map((src, i) => (
            <div key={i} className="flex flex-col items-center">
              <img src={src} alt="" className="w-12 h-12 object-contain mb-2" />
              <div className="text-sm opacity-80">
                {[
                  'мат. анализ','линал и геометрия','теор. вер. и статистика','дискретная математика','диффуры',
                  'численные методы','оптимизация','теория чисел','функц. анализ','прикладная математика'
                ][i]}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* BANK + DEMO */}
      <section className="container mx-auto px-6 py-10 grid md:grid-cols-2 gap-8 items-center">
        <div>
          <h2 className="text-3xl font-bold">Большой банк заданий</h2>
          <p className="mt-3 text-lg">
            <span className="text-primary-900 font-semibold">1000+ задач</span> на 10 тем и 3 уровня сложности.  
            Каждый найдёт что-то для себя!
          </p>
          <div className="mt-8 flex items-center gap-6">
            <img src={mascotHead} alt="" className="w-44 h-44 object-contain" />
            <div className="text-2xl font-bold">2 + 2 = <span className="bg-primary-200 px-2 rounded-md">5</span></div>
          </div>
        </div>
        <div>
          <div className="rounded-xl2 border-4 border-primary-200 p-6 max-w-md ml-auto">
            <div className="text-xl font-bold">2x + 4y = 7z</div>
          </div>
          <div className="rounded-xl2 border-4 border-primary-200 p-6 max-w-md ml-auto mt-6">
            <img src={shapesRow} alt="" className="w-full object-contain" />
          </div>
        </div>
      </section>

      {/* SUPPORTERS */}
      <section className="bg-primary-500 text-white py-12 text-center">
        <div className="container mx-auto">
          <div className="text-2xl font-semibold mb-6">Нас поддерживают</div>
          <div className="flex items-center justify-center gap-10">
            <img src={logoSber} alt="Сбер" className="h-10" />
            <img src={logoCU} alt="Центральный университет" className="h-10" />
          </div>
        </div>
      </section>

      {/* CTA footer block */}
      <section className="container mx-auto px-6 py-12 text-center">
        <img src={mascotHead} alt="" className="mx-auto w-24 h-24 mb-4" />
        <h3 className="text-2xl md:text-3xl font-bold">Прокачайте свой математический скилл с уточкой Мати!</h3>
        <div className="mt-6 flex gap-4 justify-center">
          <Button onClick={() => navigate('/auth?tab=register')}>Зарегистрироваться</Button>
          <button
            onClick={() => navigate('/auth?tab=login')}
            className="rounded-xl2 px-6 py-3 font-semibold shadow-card border-2 border-primary-500 text-primary-900 bg-white hover:bg-primary-200 transition"
          >
            Войти
          </button>
        </div>
      </section>

      {/* FOOTER (упрощённая версия из макета) */}
      <footer className="bg-primary-500 text-white py-10">
        <div className="container mx-auto px-6 grid md:grid-cols-3 gap-8">
          <div>
            <div className="text-2xl font-bold">Мати</div>
          </div>
          <div>
            <div className="text-xl font-semibold">О нас</div>
            <div className="opacity-90 mt-2">О мати<br/>Наша команда</div>
          </div>
          <div>
            <div className="text-xl font-semibold">Авторизация</div>
            <div className="opacity-90 mt-2">Вход<br/>Регистрация</div>
          </div>
        </div>
        <div className="container mx-auto px-6 mt-8 text-sm opacity-90">Terms of service · Privacy policy</div>
      </footer>
    </div>
  );
}
