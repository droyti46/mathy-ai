import { Link } from "react-router-dom";
import logoMathy from "@/assets/images/logo-mathy.png";

import nikitaIcon from '@/assets/images/nikita.png';
import andreyIcon from '@/assets/images/andrey.png';
import mariaIcon from '@/assets/images/maria.png';
import alinaIcon from '@/assets/images/alina.png';

export default function TeamPage() {
  return (
    <div className="min-h-screen bg-primary-500/90">
      <header className="bg-primary-500 text-white">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/"><img src={logoMathy} alt="Мати" className="h-7" /></Link>
          <nav className="opacity-90 text-sm space-x-6">
            <Link to="/about" className="hover:underline">О нас</Link>
            <Link to="/about/maty" className="hover:underline">О Мати</Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto max-w-4xl px-6 py-10 text-white">
        <h1 className="text-3xl font-bold">Наша команда</h1>
        {/* BANK + DEMO */}
        <section className="container mx-auto max-w-6xl px-6 py-16 space-y-16">
          {/* Первая фича */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-3xl font-bold">Никита Бакутов</h2>
              <p className="mt-3 text-lg">
                 ML Engineer, Full-Stack, Designer
              </p>
            </div>
            <div className="flex justify-center md:justify-end">
              <div className="flex items-center gap-6">
                <img src={nikitaIcon} alt="" className="w-[400px] object-contain pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Вторая фича */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div className="flex justify-center">
              <div className="flex items-center gap-6">
                <img src={andreyIcon} alt="" className="w-[600px] object-contain pointer-events-none" />
              </div>
            </div>
            <div>
              <h2 className="text-3xl font-bold">Андрей Четверяков</h2>
              <p className="mt-3 text-lg">
                ML Engineer, Backend
              </p>
            </div>
          </div>

          {/* Третья фича */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-3xl font-bold">Мария Лабецкая</h2>
              <p className="mt-3 text-lg">
                Frontend
              </p>
            </div>
            <div className="flex justify-center md:justify-end">
              <div className="flex items-center gap-6">
                <img src={mariaIcon} alt="" className="w-[600px] object-contain pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Вторая фича */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div className="flex justify-center">
              <div className="flex items-center gap-6">
                <img src={alinaIcon} alt="" className="w-[600px] object-contain pointer-events-none" />
              </div>
            </div>
            <div>
              <h2 className="text-3xl font-bold">Андрей Четверяков</h2>
              <p className="mt-3 text-lg">
                Frontend
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
