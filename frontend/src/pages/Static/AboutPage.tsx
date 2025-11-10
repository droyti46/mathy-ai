import { Link } from "react-router-dom";
import logoMathy from "@/assets/images/logo-mathy.png";

export default function AboutMatyPage() {
  return (
    <div className="min-h-screen bg-primary-500/90">
      <header className="bg-primary-500 text-white">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/"><img src={logoMathy} alt="Мати" className="h-7" /></Link>
          <nav className="opacity-90 text-sm space-x-6">
            <Link to="/about" className="hover:underline">О нас</Link>
            <Link to="/about/team" className="hover:underline">Наша команда</Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto max-w-4xl px-6 py-10 text-white">
        <h1 className="text-3xl font-bold">О Мати</h1>
        <p className="mt-4 opacity-90">
          История и персонаж утёнка Мати. Страница-заглушка для будущего контента.
        </p>
      </main>
    </div>
  );
}
