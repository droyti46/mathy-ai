import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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

type Theme = { id: string; title: string; tasks_count?: number };
type Difficulty = 'easy'|'medium'|'hard';
type Task = {
  id: string;
  theme_id: string;
  theme_title: string;
  difficulty: Difficulty;
  name: string;
  statement_md: string;
};

const LIMIT = 20;

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

export default function TasksTab() {
  const nav = useNavigate();

  // темы + прогресс
  const [themes, setThemes] = useState<Theme[]>([]);
  const [totalTasksAll, setTotalTasksAll] = useState(0);
  const [solvedAll, setSolvedAll] = useState<number>(0);

  // мультивыбор
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [selectedDiffs, setSelectedDiffs] = useState<Set<Difficulty>>(new Set());

  // поиск
  const [query, setQuery] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');

  // данные задач + пагинация
  const [tasks, setTasks] = useState<Task[]>([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  // стабильные "соединённые" фильтры
  const themesJoined = useMemo(
    () => selectedThemes.slice().sort().join(','),
    [selectedThemes]
  );
  const diffsJoined = useMemo(
    () => [...selectedDiffs].sort().join(','),
    [selectedDiffs]
  );

  // ключ фильтров (только то, что действительно определяет выбор)
  const filtersKey = useMemo(
    () => JSON.stringify({ q: debouncedQ.trim(), themes: themesJoined, diffs: diffsJoined }),
    [debouncedQ, themesJoined, diffsJoined]
  );

  // загрузка тем/прогресса
  useEffect(() => {
    (async () => {
      const tRes = await api.get<Theme[]>('/api/themes');
      setThemes(tRes.data);
      setTotalTasksAll(tRes.data.reduce((s, t) => s + (t.tasks_count ?? 0), 0));
      try {
        const { data } = await api.get<{ solved: number }>('/api/auth/me/stats');
        setSolvedAll(data.solved);
      } catch {}
    })();
  }, []);

  // дебаунс поиска
  useEffect(() => {
    const id = setTimeout(() => setDebouncedQ(query.trim()), 400);
    return () => clearTimeout(id);
  }, [query]);

  // сам загрузчик порции
  const fetchMore = useCallback(
    async ({ initial = false, force = false }: { initial?: boolean; force?: boolean } = {}) => {
      if ((!hasMore || loading) && !force) return;

      const currentOffset = initial ? 0 : offset;
      setLoading(true);

      const params: Record<string, any> = {
        limit: LIMIT,
        offset: currentOffset,
      };
      const q = debouncedQ.trim();
      if (q) params.q = q;
      if (themesJoined) params.theme_id = themesJoined;
      if (diffsJoined) params.difficulty = diffsJoined;

      const { data } = await api.get<Task[]>('/api/tasks', { params });

      setTasks((prev) => (initial ? data : prev.concat(data)));
      setOffset(currentOffset + data.length);
      setHasMore(data.length === LIMIT);
      setLoading(false);
    },
    [hasMore, loading, offset, debouncedQ, themesJoined, diffsJoined]
  );

  // стабильная ссылка на fetchMore для эффектов без зависимостей
  const fetchMoreRef = useRef(fetchMore);
  useEffect(() => { fetchMoreRef.current = fetchMore; }, [fetchMore]);

  // Смена фильтров -> сброс и первая загрузка
  useEffect(() => {
    setTasks([]);
    setOffset(0);
    setHasMore(true);
    setLoading(false);
    // важно: НЕ зависеть от fetchMore в массиве deps
    fetchMoreRef.current?.({ initial: true, force: true });
  }, [filtersKey]);

  // Бесконечная прокрутка (стабильный observer)
  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;

    const io = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        fetchMoreRef.current?.();
      }
    }, { rootMargin: '400px' });

    io.observe(el);
    return () => io.disconnect();
  }, []); // никаких зависимостей

  // Прогресс «x / y Решено»
  const yTotal = useMemo(() => {
    if (selectedThemes.length === 0) return totalTasksAll;
    return themes
      .filter((t) => selectedThemes.includes(t.id))
      .reduce((s, t) => s + (t.tasks_count ?? 0), 0);
  }, [selectedThemes, themes, totalTasksAll]);

  const xSolved = solvedAll;

  // переключатели
  const toggleTheme = (id: string) => {
    if (id === '__ALL__') {
      setSelectedThemes([]);
      return;
    }
    setSelectedThemes((prev) => {
      const next = prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id];
      const allIds = themes.map((t) => t.id);
      return next.length === allIds.length ? [] : next;
    });
  };

  const toggleDiff = (d: Difficulty | '__ANY__') => {
    if (d === '__ANY__') {
      setSelectedDiffs(new Set());
      return;
    }
    setSelectedDiffs((prev) => {
      const next = new Set(prev);
      next.has(d) ? next.delete(d) : next.add(d);
      return next.size === 3 ? new Set() : next;
    });
  };

  return (
    <div className="text-white">
      {/* Фильтры */}
      <div className="space-y-6">
        <h3 className="text-2xl font-bold">Темы</h3>
        <div className="flex flex-wrap gap-4">
          <ThemeChip label="Все задачи" active={selectedThemes.length === 0} onClick={() => toggleTheme('__ALL__')} />
          {themes.map((t) => (
            <ThemeChip
              key={t.id}
              icon={ICON_BY_THEME_ID[t.id]}
              label={t.title}
              active={selectedThemes.includes(t.id)}
              onClick={() => toggleTheme(t.id)}
            />
          ))}
        </div>

        <h3 className="text-2xl font-bold">Уровни сложности</h3>
        <div className="flex flex-wrap gap-4 items-center">
          <LevelChip label="Любая сложность" active={selectedDiffs.size === 0} onClick={() => toggleDiff('__ANY__')} />
          <LevelChip label="Лёгкий" active={selectedDiffs.has('easy')} onClick={() => toggleDiff('easy')} stars={1} />
          <LevelChip label="Средний" active={selectedDiffs.has('medium')} onClick={() => toggleDiff('medium')} stars={2} />
          <LevelChip label="Сложный" active={selectedDiffs.has('hard')} onClick={() => toggleDiff('hard')} stars={3} />
        </div>

        {/* Поиск + прогресс */}
        <div className="flex items-center gap-6">
          <div className="flex-1 rounded-full px-4 py-2 flex items-center gap-3 bg-primary-900/20">
            <span className="opacity-80">🔍</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Поиск заданий"
              className="bg-transparent outline-none w-full placeholder-white/70"
            />
          </div>
          <div className="text-right whitespace-nowrap opacity-95">
            <span className="font-semibold">{xSolved}</span>/<span className="opacity-90">{yTotal}</span> Решено
          </div>
        </div>
      </div>

      {/* Список задач */}
      <div className="mt-8 space-y-4">
        {tasks.map((t, i) => (
          <TaskRow key={t.id} task={t} even={i % 2 === 1} onClick={() => nav(`/task/${t.id}`)} />
        ))}
        {loading && <div className="text-center py-6 opacity-90">Загрузка…</div>}
        <div ref={sentinelRef} className="h-2" />
        {!hasMore && tasks.length > 0 && (
          <div className="text-center py-6 opacity-80">Это все задачи по выбранным фильтрам</div>
        )}
      </div>
    </div>
  );
}

// UI

function ThemeChip({
  label,
  icon,
  active,
  onClick,
}: {
  label: string;
  icon?: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={
        'flex items-center gap-3 px-5 py-3 rounded-xl2 transition hover:scale-105 ' +
        (active
          ? 'bg-white text-black'
          : 'bg-[#5C5C5C] text-[#999999]')
      }
    >
      {icon && <img src={icon} alt="" className="w-[60px] object-contain" />}
      <span className="text-lg">{label}</span>
    </button>
  );
}

function LevelChip({
  label, active, onClick, stars = 0,
}: { label: string; active?: boolean; onClick?: () => void; stars?: 0|1|2|3 }) {
  return (
    <button
      onClick={onClick}
      className={
        'flex items-center gap-3 px-5 py-2 rounded-full bg-primary-900/30 hover:scale-105 transition ' +
        (active ? 'ring-2 ring-white' : '')
      }
    >
      {stars > 0 && (
        <span aria-hidden className="text-xl">
          {'★'.repeat(stars)}{'☆'.repeat(3 - stars)}
        </span>
      )}
      <span>{label}</span>
    </button>
  );
}

function TaskRow({ task, even, onClick }: { task: Task; even: boolean; onClick: () => void }) {
  const icon = ICON_BY_THEME_ID[task.theme_id];
  return (
    <div
      onClick={onClick}
      className={
        'cursor-pointer rounded-xl2 bg-white text-neutral-900 flex items-center justify-between px-6 py-4 ' +
        (even ? 'bg-primary-200/40' : '')
      }
    >
      <div className="pr-4 max-w-[60%]">
        <div className="opacity-90">
          <b>{task.name}</b>
          <div className="mt-1 md-snippet">
            <Markdown>{task.statement_md}</Markdown>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-8">
        <div className="text-primary-900 text-xl">{starsByDifficulty(task.difficulty)}</div>
        <div className="flex items-center gap-3 text-right">
          {icon && <img src={icon} alt="" className="w-[100px] object-contain" />}
          <div className="text-sm">{task.theme_title}</div>
        </div>
      </div>
    </div>
  );
}

function starsByDifficulty(d: Difficulty) {
  const s = d === 'easy' ? 1 : d === 'medium' ? 2 : 3;
  return '★'.repeat(s) + '☆'.repeat(3 - s);
}

function snippet(md: string, n = 160) {
  const text = md.replace(/\s+/g, ' ').replace(/[#_*`$\\]/g, '');
  return text.length > n ? text.slice(0, n - 1) + '…' : text;
}
