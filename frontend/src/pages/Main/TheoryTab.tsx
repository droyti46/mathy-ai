import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api/axios';
import Markdown from '@/components/Markdown';

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

type TheoryLesson = {
  id: string;
  title: string;
  description?: string | null;
  tasks_count?: number;
  theme_id: string;
};

type TheoryTheme = {
  id: string;
  title: string;
  description?: string | null;
  tasks_count?: number;
  lessons: TheoryLesson[];
};

const ICON_BY_TITLE: Record<string, string> = {
  'Математический анализ': icon1,
  'Линейная алгебра и геометрия': icon2,
  'Теория вероятностей и статистика': icon3,
  'Дискретная математика': icon4,
  'Дифференциальные уравнения': icon5,
  'Численные методы': icon6,
  'Оптимизация': icon7,
  'Теория чисел': icon8,
  'Функциональный анализ': icon9,
  'Прикладная математика': icon10,
  'Геометрия (дополнение)': icon2,
};

// заданный порядок разделов
const THEMES_ORDER = [
  'Математический анализ',
  'Линейная алгебра и геометрия',
  'Теория вероятностей и статистика',
  'Дискретная математика',
  'Дифференциальные уравнения',
  'Численные методы',
  'Оптимизация',
  'Теория чисел',
  'Функциональный анализ',
  'Прикладная математика',
  'Геометрия (дополнение)',
];
const orderIndex = new Map(THEMES_ORDER.map((t, i) => [t, i]));

export default function TheoryTab() {
  const [tree, setTree] = useState<TheoryTheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set()); // theme.id -> collapsed
  const navigate = useNavigate();

  useEffect(() => {
    let canceled = false;
    (async () => {
      try {
        const { data } = await api.get<TheoryTheme[]>('/api/theory/tree');
        if (canceled) return;

        // сортировка разделов по заданному порядку + уроков по возрастанию id
        const sorted = data
          .slice()
          .sort((a, b) => (orderIndex.get(a.title) ?? 999) - (orderIndex.get(b.title) ?? 999))
          .map((t) => ({
            ...t,
            lessons: t.lessons
              .slice()
              .sort((l1, l2) => Number(l1.id) - Number(l2.id)),
          }));

        setTree(sorted);
        // по умолчанию ВСЕ свернуты
        setCollapsed(new Set(sorted.map((t) => t.id)));
      } finally {
        setLoading(false);
      }
    })();
    return () => {
      canceled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return tree;
    return tree
      .map((t) => ({
        ...t,
        lessons: t.lessons.filter(
          (l) =>
            l.title.toLowerCase().includes(query) ||
            t.title.toLowerCase().includes(query)
        ),
      }))
      .filter((t) => t.lessons.length > 0);
  }, [tree, q]);

  const toggleTheme = (id: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const expandAll = () => setCollapsed(new Set()); // всё развернуть
  const collapseAll = () => setCollapsed(new Set(tree.map((t) => t.id))); // всё свернуть

  return (
    <div className="text-white">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Теория</h1>
          <p className="opacity-80 mt-1">Изучай темы блоками и ныряй в уроки в один клик</p>
        </div>
        <div className="w-full md:w-[520px] flex gap-3">
          <div className="flex-1 flex items-center gap-3 bg-white/10 rounded-full px-5 py-3 backdrop-blur">
            <span>🔎</span>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Поиск по темам и урокам…"
              className="bg-transparent outline-none w-full placeholder-white/70"
            />
            {q && (
              <button
                onClick={() => setQ('')}
                className="text-white/70 hover:text-white transition"
                aria-label="Очистить"
              >
                ✕
              </button>
            )}
          </div>
          <button onClick={expandAll} className="px-4 py-3 rounded-full bg-white/10 hover:bg-white/20 transition">
            Развернуть
          </button>
          <button onClick={collapseAll} className="px-4 py-3 rounded-full bg-white/10 hover:bg-white/20 transition">
            Свернуть
          </button>
        </div>
      </div>

      {/* Скелетон */}
      {loading && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-2xl bg-white/10 h-40 animate-pulse" />
          ))}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="mt-10 text-white/80">Ничего не найдено по запросу «{q}»</div>
      )}

      {/* Темы */}
      {!loading && filtered.length > 0 && (
        <div className="mt-8 space-y-8">
          {filtered.map((theme) => {
            const isCollapsed = collapsed.has(theme.id);
            return (
              <section key={theme.id} className="rounded-2xl bg-white/8 border border-white/10">
                {/* Заголовок темы — кликабелен, сворачивает */}
                <button
                  onClick={() => toggleTheme(theme.id)}
                  className="w-full flex items-center gap-4 p-4"
                >
                  {/* Иконка в белой рамке */}
                  <div className="shrink-0 px-2 py-2 rounded-xl bg-white border border-white/30 grid place-items-center">
                    {ICON_BY_TITLE[theme.title] && (
                      <img
                        src={ICON_BY_TITLE[theme.title]}
                        alt=""
                        className="w-[100px] object-contain"
                      />
                    )}
                  </div>
                  <div className="text-left flex-1">
                    <h2 className="text-xl font-bold">{theme.title}</h2>
                    {theme.description && (
                      <p className="text-white/80 text-sm mt-0.5">{theme.description}</p>
                    )}
                  </div>
                  <span className="text-white/70">{isCollapsed ? '▸' : '▾'}</span>
                </button>

                {/* Список уроков */}
                {!isCollapsed && (
                  <div className="px-4 pb-4">
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {theme.lessons.map((lesson) => (
                        <button
                          key={lesson.id}
                          onClick={() => navigate(`/app/theory/${theme.id}/${lesson.id}`)}
                          className="group text-left rounded-2xl bg-white text-neutral-900 p-5 transition"
                        >
                          <div className="font-semibold leading-snug">{lesson.title}</div>
                          <div className="mt-2 text-xs text-neutral-600">
                            Урок {lesson.id.padStart(3, '0')}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
