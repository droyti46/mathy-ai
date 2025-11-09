import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api/axios';
import Markdown from '@/components/Markdown';
import Button from '@/components/Button';

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

// Types
export type Difficulty = 'easy' | 'medium' | 'hard';
export type Task = {
  id: string;
  theme_id: string;
  theme_title: string;
  lesson_id?: string;
  lesson_title?: string;
  difficulty: Difficulty;
  name: string;
  statement_md: string;
  source?: string;
  tags?: string[];
};

type DailyResponse = {
  date: string; // YYYY-MM-DD
  task: Task | null;
};

const ICON_BY_THEME_ID: Record<string, string> = {
  'мат-анализ': icon1,
  'линал-и-геометрия': icon2,
  'теор-вер-и-статистика': icon3,
  'дискретная-математика': icon4,
  'дифференциальные-уравнения': icon5,
  'численные-методы': icon6,
  'оптимизация': icon7,
  'теория-чисел': icon8,
  'функ-анализ': icon9,
  'прикладная-математика': icon10,
};

export default function DailyTab() {
  const nav = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [daily, setDaily] = useState<DailyResponse | null>(null);

  // countdown до следующего ежедневного задания (локальное время пользователя)
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const msLeft = useMemo(() => msUntilTomorrow(now), [now]);
  const timeLeft = useMemo(() => formatDuration(msLeft), [msLeft]);

  const fetchDaily = async () => {
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.get<DailyResponse>('/api/tasks/daily');
      setDaily(data);
    } catch (e: any) {
      setError('Не удалось загрузить ежедневную задачу. Попробуйте ещё раз.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get<DailyResponse>('/api/tasks/daily');
        if (cancelled) return;
        setDaily(data);
      } catch {
        if (!cancelled) setError('Не удалось загрузить ежедневную задачу.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const onOpenTask = () => {
    if (!daily?.task) return;
    nav(`/task/${daily.task.id}`);
  };

  return (
    <div className="text-white">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">Ежедневная задача</h1>
          <p className="mt-1 opacity-80 text-sm md:text-base">
            Обновляется каждый день в 00:00. До следующей: <b className="opacity-95">{timeLeft}</b>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={fetchDaily}
            className="px-4 py-2 rounded-full text-sm bg-primary-900/60 ring-1 ring-white/10 hover:bg-primary-900/70"
          >
            Обновить
          </Button>
        </div>
      </header>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        {/* Карточка задачи */}
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary-900/50 to-primary-900/30 backdrop-blur-md border border-white/10">
          <Decor />

          <div className="relative p-6 md:p-8">
            {loading && <DailySkeleton />}

            {!loading && error && (
              <div className="text-red-200">
                <div className="text-lg font-semibold">{error}</div>
                <div className="opacity-80 mt-2 text-sm">Проверьте подключение к сети и повторите попытку.</div>
                <Button
                  onClick={fetchDaily}
                  className="mt-4 bg-primary-900/80 ring-1 ring-white/10 hover:bg-primary-900/90"
                >
                  Повторить загрузку
                </Button>
              </div>
            )}

            {!loading && !error && daily?.task && (
              <div className="space-y-6">
                {/* Верхняя панель: дата, тема, сложность */}
                <div className="flex flex-wrap items-center gap-3">
                  <Pill icon="📅">{formatDate(daily.date)}</Pill>
                  <ThemePill themeId={daily.task.theme_id} themeTitle={daily.task.theme_title} />
                  <DifficultyPill difficulty={daily.task.difficulty} />
                </div>

                <h2 className="text-2xl md:text-3xl font-bold leading-tight">{daily.task.name}</h2>

                <div className="prose prose-invert max-w-none text-white/95">
                  <Markdown>{daily.task.statement_md}</Markdown>
                </div>

                <div className="flex flex-wrap gap-3 pt-2">
                  <Button
                    onClick={onOpenTask}
                    className="bg-black/60 hover:bg-black/70"
                  >
                    Открыть задачу
                  </Button>
                </div>

                {!!(daily.task.tags && daily.task.tags.length) && (
                  <div className="pt-2 flex flex-wrap gap-2">
                    {daily.task.tags!.map((t) => (
                      <span key={t} className="text-xs px-2 py-1 rounded-full bg-white/10">#{t}</span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {!loading && !error && !daily?.task && (
              <div className="text-white/90">
                <div className="text-2xl font-bold">Сегодня задания нет</div>
                <div className="opacity-80 mt-2">Загляните позже или обновите страницу.</div>
              </div>
            )}
          </div>
        </section>

        {/* Боковая панель: метаданные/подсказки */}
        <aside className="rounded-3xl bg-primary-900/30 border border-white/10 p-6 lg:p-8 space-y-6">
          <h3 className="text-xl font-bold">Подсказки и метаданные</h3>

          {/* Когда обновляется */}
          <InfoCard title="Когда обновляется?">
            Новая задача появляется каждый день в <b>00:00</b> (по вашему локальному времени).
          </InfoCard>

          {/* Сложность */}
          {daily?.task && (
            <InfoCard title="Сложность">
              <div className="flex items-center gap-2">
                <span className="text-lg" aria-hidden>{starsByDifficulty(daily.task.difficulty)}</span>
                <span className="opacity-95">{difficultyText(daily.task.difficulty)}</span>
              </div>
            </InfoCard>
          )}

          {/* Тема */}
          {daily?.task && (
            <div className="rounded-2xl bg-white/5 border border-white/10 p-4">
              <div className="text-sm opacity-80">Тема</div>
              <div className="flex items-center gap-3 mt-1">
                <img
                  src={ICON_BY_THEME_ID[daily.task.theme_id]}
                  alt=""
                  className="w-[70px] object-contain"
                />
                <div className="font-semibold">{daily.task.theme_title}</div>
              </div>
              {daily.task.lesson_title && (
                <div className="mt-3 text-sm opacity-85">
                  Раздел курса: <span className="opacity-95">{daily.task.lesson_title}</span>
                </div>
              )}
            </div>
          )}

          {/* До следующей задачи */}
          <div className="rounded-2xl bg-gradient-to-br from-primary-900/40 to-primary-900/20 border border-white/10 p-4">
            <div className="text-sm opacity-80">До следующей задачи</div>
            <div className="text-2xl font-bold mt-1 tracking-tight">{timeLeft}</div>
          </div>
        </aside>
      </div>
    </div>
  );
}

// ---------- UI bits ----------
function Pill({ icon, children }: { icon?: string; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 text-sm">
      {icon && <span aria-hidden>{icon}</span>}
      <span>{children}</span>
    </span>
  );
}

function DifficultyPill({ difficulty }: { difficulty: Difficulty }) {
  const text = difficultyText(difficulty);
  return (
    <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-900/40 text-sm ring-1 ring-white/10">
      <span className="text-base" aria-hidden>{starsByDifficulty(difficulty)}</span>
      <span className="opacity-95">{text}</span>
    </span>
  );
}

function difficultyText(difficulty: Difficulty) {
  return difficulty === 'easy' ? 'Лёгкий' : difficulty === 'medium' ? 'Средний' : 'Сложный';
}

function ThemePill({ themeId, themeTitle }: { themeId: string; themeTitle: string }) {
  const icon = ICON_BY_THEME_ID[themeId];
  return (
    <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 text-sm">
      {icon && <img src={icon} alt="" className="w-5 h-5 object-contain" />}
      <span>{themeTitle}</span>
    </span>
  );
}

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl bg-white/5 border border-white/10 p-4">
      <div className="font-semibold">{title}</div>
      <div className="mt-1 opacity-85 text-sm leading-relaxed">{children}</div>
    </div>
  );
}

function DailySkeleton() {
  return (
    <div className="animate-pulse">
      <div className="flex flex-wrap gap-3">
        <SkPill w="w-28" />
        <SkPill w="w-40" />
        <SkPill w="w-44" />
      </div>
      <div className="h-8 md:h-10 bg-white/10 rounded-xl mt-5 w-3/4" />
      <div className="space-y-3 mt-5">
        <div className="h-4 bg-white/10 rounded" />
        <div className="h-4 bg-white/10 rounded" />
        <div className="h-4 bg-white/10 rounded w-2/3" />
      </div>
      <div className="flex gap-3 mt-6">
        <div className="h-11 w-40 bg-white/10 rounded-xl" />
        <div className="h-11 w-48 bg-white/10 rounded-xl" />
      </div>
    </div>
  );
}

function SkPill({ w = 'w-28' }: { w?: string }) {
  return <div className={`h-7 ${w} bg-white/10 rounded-full`} />;
}

function Decor() {
  return (
    <>
      {/* мягкие засветы, приглушённые чтобы убрать пересвет */}
      <div className="pointer-events-none absolute -top-24 -left-24 h-72 w-72 rounded-full bg-primary-200/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-primary-100/10 blur-3xl" />
      {/* тонкая сетка */}
      <svg className="pointer-events-none absolute inset-0 opacity-5" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M 32 0 L 0 0 0 32" fill="none" stroke="currentColor" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>
    </>
  );
}

// ---------- Utils ----------
function starsByDifficulty(d: Difficulty) {
  const s = d === 'easy' ? 1 : d === 'medium' ? 2 : 3;
  return '★'.repeat(s) + '☆'.repeat(3 - s);
}

function msUntilTomorrow(now = new Date()) {
  const next = new Date(now);
  next.setHours(24, 0, 0, 0); // локальная полночь
  return Math.max(0, next.getTime() - now.getTime());
}

function formatDuration(ms: number) {
  const total = Math.floor(ms / 1000);
  const h = Math.floor(total / 3600).toString().padStart(2, '0');
  const m = Math.floor((total % 3600) / 60).toString().padStart(2, '0');
  const s = Math.floor(total % 60).toString().padStart(2, '0');
  return `${h}:${m}:${s}`;
}

function formatDate(yyyyMMdd: string) {
  // ожидаем формát YYYY-MM-DD
  const [y, m, d] = yyyyMMdd.split('-').map(Number);
  const date = new Date(y, (m || 1) - 1, d || 1);
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric',
  });
}
