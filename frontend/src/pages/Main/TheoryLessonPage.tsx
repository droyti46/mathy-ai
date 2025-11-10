import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
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

type TheoryLessonEntry = {
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
  lessons: TheoryLessonEntry[];
};
type TheoryLessonFull = {
  theme_id: string;
  theme_title: string;
  lesson_id: string;
  title: string;
  content_md: string;
};

type Difficulty = 'easy' | 'medium' | 'hard';
type Task = {
  id: string;
  theme_id: string;
  theme_title: string;
  difficulty: Difficulty;
  name: string;
  statement_md: string;
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

function starsByDifficulty(d: Difficulty) {
  const s = d === 'easy' ? 1 : d === 'medium' ? 2 : 3;
  return '★'.repeat(s) + '☆'.repeat(3 - s);
}
function snippet(md: string, n = 160) {
  const text = md.replace(/\s+/g, ' ').replace(/[#_*`$\\]/g, '');
  return text.length > n ? text.slice(0, n - 1) + '…' : text;
}

const TASK_THEME_ID_BY_TITLE: Record<string, string> = {
  'Математический анализ': 'мат-анализ',
  'Линейная алгебра и геометрия': 'линал-и-геометрия',
  'Теория вероятностей и статистика': 'теор-вер-и-статистика',
  'Дискретная математика': 'дискретная-математика',
  'Дифференциальные уравнения': 'дифференциальные-уравнения',
  'Численные методы': 'численные-методы',
  'Оптимизация': 'оптимизация',
  'Теория чисел': 'теория-чисел',
  'Функциональный анализ': 'функ-анализ',
  'Прикладная математика': 'прикладная-математика',
  'Геометрия (дополнение)': 'линал-и-геометрия',
};

export default function TheoryLessonPage() {
  const { themeId, lessonId } = useParams<{ themeId: string; lessonId: string }>();
  const navigate = useNavigate();

  const [tree, setTree] = useState<TheoryTheme[]>([]);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [lesson, setLesson] = useState<TheoryLessonFull | null>(null);
  const [loadingLesson, setLoadingLesson] = useState(true);
  const [loadingTree, setLoadingTree] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

  const [tasks, setTasks] = useState<Task[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);

  // load tree (с сортировкой и свёртыванием тем; текущую — разворачиваем)
  useEffect(() => {
    let canceled = false;
    (async () => {
      try {
        const { data } = await api.get<TheoryTheme[]>('/api/theory/tree');
        if (canceled) return;

        const sorted = data
          .slice()
          .sort((a, b) => (orderIndex.get(a.title) ?? 999) - (orderIndex.get(b.title) ?? 999))
          .map((t) => ({
            ...t,
            lessons: t.lessons.slice().sort((l1, l2) => Number(l1.id) - Number(l2.id)),
          }));

        setTree(sorted);

        const allCollapsed = new Set(sorted.map((t) => t.id));
        if (themeId) allCollapsed.delete(themeId); // показываем активную тему
        setCollapsed(allCollapsed);
      } finally {
        if (!canceled) setLoadingTree(false);
      }
    })();
    return () => { canceled = true; };
  }, [themeId]);

  // load lesson
  useEffect(() => {
    let canceled = false;
    setLoadingLesson(true);
    (async () => {
      try {
        const { data } = await api.get<TheoryLessonFull>(`/api/theory/${themeId}/${lessonId}`);
        if (!canceled) setLesson(data);
      } finally {
        if (!canceled) setLoadingLesson(false);
      }
    })();
    return () => { canceled = true; };
  }, [themeId, lessonId]);

  // task suggestions
  useEffect(() => {
    let canceled = false;
    (async () => {
      if (!lesson) return;
      const tasksThemeId = TASK_THEME_ID_BY_TITLE[lesson.theme_title];
      if (!tasksThemeId) return;
      setLoadingTasks(true);
      try {
        const { data } = await api.get<Task[]>('/api/tasks', {
          params: { limit: 6, offset: 0, theme_id: tasksThemeId },
        });
        if (!canceled) setTasks(data);
      } finally {
        if (!canceled) setLoadingTasks(false);
      }
    })();
    return () => { canceled = true; };
  }, [lesson]);

  const currentTheme = useMemo(
    () => tree.find((t) => t.id === themeId),
    [tree, themeId]
  );

  const activeRef = useRef<HTMLButtonElement | null>(null);
  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, [themeId, lessonId, loadingTree]);

  const toggleTheme = (id: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="text-white grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
      {/* Sidebar */}
      <aside className={(sidebarOpen ? 'block' : 'hidden') + ' lg:block'}>
        <div className="sticky top-4 rounded-2xl bg-white/8 backdrop-blur border border-white/10">
          <div className="flex items-center justify-between p-4">
            <div className="font-semibold">Дерево теории</div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden text-white/70 hover:text-white"
              aria-label="Скрыть дерево"
            >
              Скрыть
            </button>
          </div>
          <div className="max-h-[70vh] overflow-auto px-2 pb-3">
            {loadingTree ? (
              <div className="p-4 text-white/80">Загрузка…</div>
            ) : (
              <nav className="space-y-3 pr-2">
                {tree.map((t) => {
                  const isCollapsed = collapsed.has(t.id);
                  return (
                    <div key={t.id} className="px-2">
                      {/* Заголовок темы (сворачиваемый) */}
                      <button
                        onClick={() => toggleTheme(t.id)}
                        className="w-full flex items-center gap-3 px-2 py-2 rounded-xl hover:bg-white/10 transition"
                      >
                        <span className="text-white/70">{isCollapsed ? '▸' : '▾'}</span>
                        <div className="shrink-0 rounded-lg bg-white border border-white/30 grid place-items-center">
                          {ICON_BY_TITLE[t.title] && (
                            <img src={ICON_BY_TITLE[t.title]} alt="" className="w-[60px] object-contain" />
                          )}
                        </div>
                        <div className="font-medium text-left">{t.title}</div>
                      </button>

                      {/* Уроки */}
                      {!isCollapsed && (
                        <div className="ml-8 mt-1 space-y-1">
                          {t.lessons.map((l) => {
                            const isActive = t.id === themeId && l.id === lessonId;
                            return (
                              <button
                                key={l.id}
                                ref={isActive ? activeRef : undefined}
                                onClick={() => navigate(`/app/theory/${t.id}/${l.id}`)}
                                className={
                                  'w-full text-left px-3 py-2 rounded-xl transition ' +
                                  (isActive
                                    ? 'bg-white text-neutral-900'
                                    : 'hover:bg-white/10 text-white/90')
                                }
                              >
                                <span className="text-xs opacity-70 mr-2">
                                  {String(l.id).padStart(3, '0')}
                                </span>
                                {l.title}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </nav>
            )}
          </div>
        </div>
      </aside>

      {/* Content */}
      <section>
        {/* top bar */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/app/theory')}
              className="rounded-full bg-white/10 hover:bg-white/20 px-4 py-2 transition"
            >
              ← Ко всем темам
            </button>
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              className="lg:hidden rounded-full bg-white/10 hover:bg-white/20 px-3 py-2 transition"
            >
              {sidebarOpen ? 'Скрыть дерево' : 'Показать дерево'}
            </button>
          </div>

          {currentTheme && ICON_BY_TITLE[currentTheme.title] && (
            <div className="hidden sm:flex items-center gap-2 text-white/80">
              <div className="rounded-md bg-white border border-white/30 grid place-items-center">
                <img
                  src={ICON_BY_TITLE[currentTheme.title]}
                  alt=""
                  className="w-[60px] object-contain"
                />
              </div>
              <span className="text-sm">{currentTheme.title}</span>
            </div>
          )}
        </div>

        {/* lesson */}
        <article className="mt-6 rounded-2xl bg-white text-neutral-900 p-6 md:p-8">
          {loadingLesson || !lesson ? (
            <div className="animate-pulse space-y-3">
              <div className="h-8 bg-neutral-200 rounded w-2/3" />
              <div className="h-4 bg-neutral-200 rounded w-1/3" />
              <div className="h-48 bg-neutral-100 rounded" />
            </div>
          ) : (
            <>
              <header className="mb-3">
                <div className="text-sm text-neutral-500 mb-1">
                  Раздел: {lesson.theme_title} · Урок {String(lesson.lesson_id).padStart(3, '0')}
                </div>
                <h1 className="text-2xl md:text-3xl font-extrabold leading-tight">
                  {lesson.title}
                </h1>
              </header>

              <div className="prose max-w-none prose-headings:scroll-mt-24">
                <Markdown>{lesson.content_md}</Markdown>
              </div>
            </>
          )}
        </article>

        {/* tasks suggestions */}
        <div className="mt-8">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xl font-bold">Готовы закрепить?</h3>
            <Link
              to="/app/tasks"
              className="text-white/80 hover:text-white underline decoration-white/30"
            >
              Открыть все задачи
            </Link>
          </div>

          {loadingTasks && (
            <div className="grid gap-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-[92px] rounded-2xl bg-white/10 animate-pulse" />
              ))}
            </div>
          )}

          {!loadingTasks && tasks.length === 0 && (
            <div className="text-white/80">Задачи по этой теме скоро появятся.</div>
          )}

          {!loadingTasks && tasks.length > 0 && (
            <div className="space-y-3">
              {tasks.map((t, i) => (
                <TaskRow
                  key={t.id}
                  task={t}
                  even={i % 2 === 1}
                  onClick={() => navigate(`/task/${t.id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

// ===== UI: TaskRow (без теней, максимально близко к существующему стилю) =====
function TaskRow({
  task,
  even,
  onClick,
}: {
  task: Task;
  even: boolean;
  onClick: () => void;
}) {
  const icon =
    ICON_BY_TITLE[task.theme_title] ??
    ICON_BY_TITLE['Математический анализ'];

  const className =
    'cursor-pointer rounded-2xl flex items-center justify-between px-6 py-4 transition ' +
    (even ? 'bg-white text-neutral-900' : 'bg-white text-neutral-900');

  return (
    <div onClick={onClick} className={className}>
      <div className="pr-4 max-w-[60%]">
        <b className="block">{task.name}</b>
        <div className="mt-1 md-snippet text-neutral-700">
          <Markdown>{task.statement_md}</Markdown>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-neutral-800 text-lg whitespace-nowrap">
          {starsByDifficulty(task.difficulty)}
        </div>
        <div className="flex items-center gap-3 text-right">
          {icon && (
            <div className="w-[60px] h-[60px] rounded-xl bg-white border border-neutral-200 grid place-items-center">
              <img src={icon} alt="" className="w-9 h-9 object-contain" />
            </div>
          )}
          <div className="text-sm text-neutral-600">{task.theme_title}</div>
        </div>
      </div>
    </div>
  );
}
