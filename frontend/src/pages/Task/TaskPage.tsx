import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '@/lib/api/axios';
import { fetchWithAuthOnce, streamText } from '@/lib/api/stream';
import { createStreamMerger } from '@/lib/api/stream_delta';
import { CopyButton } from '@/components/CopyButton'
import { AnimatePresence, motion } from 'framer-motion';

import Button from '@/components/Button';
import Markdown from '@/components/Markdown';
import SolveLayout from './SolveMode/SolveLayout';

import mascotFace from '@/assets/images/mascot-face.png';
import reloadIcon from '@/assets/images/reload.png';
import sendIcon from '@/assets/images/send-message.png';
import ducklar from '@/assets/images/ducklar.png';
import clockIcon from '@/assets/images/clock.png';
import errorIcon from '@/assets/images/error.png';
import mascotFaceWithoutPupils from '@/assets/images/mascot-face-without-pupils.png';
import MascotEyes from "@/components/MascotEyes";

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

const META_MARK = '[[META]]';
const pane = {
  initial: { opacity: 0, x: 24, filter: 'blur(6px)' },
  animate: { opacity: 1, x: 0, filter: 'blur(0px)' },
  exit:    { opacity: 0, x: -24, filter: 'blur(6px)' },
  transition: { type: 'spring', stiffness: 400, damping: 40, mass: 0.8 },
};


type Difficulty = 'easy'|'medium'|'hard';

type Task = {
  id: string;
  theme_id: string;
  theme_title?: string | null;
  difficulty: Difficulty;
  name: string;
  statement_md: string;
};

type Span = { start: number; end: number; message?: string; severity?: 'info'|'warning'|'error'|string };
type Attempt = {
  id: string;
  task_id: string;
  solution_text: string;
  feedback: { spans_detail: Span[] };
  created_at: string;
  is_solved: boolean;
  coins_rewarded: number;
  stats?: { coins?: number };
};

type ChatMessage = { role: 'user'|'assistant'|'system'; content: string };
type ChatOut = { messages: ChatMessage[] };
type TeacherOut = {
  task_id: string;
  messages: ChatMessage[];
  is_solved?: boolean;
  coins_rewarded?: number;
  stats?: { coins?: number };
};

export default function TaskPage() {
  const nav = useNavigate();
  const { taskId = '' } = useParams();
  const [task, setTask] = useState<Task | null>(null);

  // режимы
  const [mode, setMode] = useState<'solve'|'teach'>('solve');

  // ====== Left tabs ======
  type LeftTab = 'problem' | 'attempts' | 'buy';
  const [leftTab, setLeftTab] = useState<LeftTab>('problem');

  // ====== Attempts ======
  const [attempts, setAttempts] = useState<Attempt[] | null>(null);
  const [selectedAttempt, setSelectedAttempt] = useState<Attempt | null>(null);

  // ====== Editor ======
  const [solution, setSolution] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // ====== Assistant (solve) ======
  const [assistantMsgs, setAssistantMsgs] = useState<ChatMessage[]>([]);
  const [assistantInput, setAssistantInput] = useState('');
  const [assistantLoading, setAssistantLoading] = useState(false);

  // ====== Teacher (teach) ======
  const [teacherMsgs, setTeacherMsgs] = useState<ChatMessage[]>([]);
  const [teacherStarted, setTeacherStarted] = useState(false);
  const [teacherInput, setTeacherInput] = useState('');
  const [teacherLoading, setTeacherLoading] = useState(false);

  // ====== Congrats modal ======
  const [congrats, setCongrats] = useState<{ coins: number } | null>(null);

  // ====== Реф для блокировки учителя ======
  const teacherLockRef = useRef(false);

  // ====== Реф для актуального списка ======
  const attemptsRef = useRef<Attempt[] | null>(null);
  useEffect(() => { attemptsRef.current = attempts; }, [attempts]);

  useEffect(() => {
    (async () => {
      const { data } = await api.get<Task>(`/api/tasks/${taskId}`);
      setTask(data);
    })();
  }, [taskId]);

  // Переключение в режим преподавания прячет вкладку «Мои посылки»
  useEffect(() => {
    if (mode === 'teach' && leftTab === 'attempts') setLeftTab('problem');
  }, [mode, leftTab]);

  // Живые попытки: initial + smart polling (+ optional SSE)
  useEffect(() => {
    if (leftTab !== 'attempts' || !taskId) return;

    let stopped = false;
    let timer: number | null = null;
    let es: EventSource | null = null;

    const initial = async () => {
      const [server, cached] = await Promise.all([
        api.get<Attempt[]>(`/api/tasks/${taskId}/attempts`).then(r => r.data).catch(() => []),
        Promise.resolve(loadPendingFromLS(taskId)),
      ]);
      setAttempts(prev => mergeAttempts(mergeAttempts(prev, cached), server));
      setSelectedAttempt(null);
    };

    const oneTick = async () => {
      if (stopped) return;
      try {
        const { data } = await api.get<Attempt[]>(`/api/tasks/${taskId}/attempts`);
        setAttempts(prev => {
          const merged = mergeAttempts(prev, data);
          // обновим справа открытые детали
          setSelectedAttempt(sel => sel ? (merged.find(a => a.id === sel.id) ?? sel) : null);
          // поддержим локальный кэш незавершённых
          savePendingToLS(taskId, merged);
          return merged;
        });
      } finally {
        // динамическая частота: чаще, пока есть "Проверка"
        const hasChecking = (attemptsRef.current ?? []).some(isAttemptChecking);
        const interval = document.hidden ? 15000 : (hasChecking ? 2000 : 10000);
        timer = window.setTimeout(oneTick, interval);
      }
    };

    // стартуем
    initial().then(oneTick);

    // пауза/резюм по видимости вкладки
    const onVis = () => {
      if (timer) { clearTimeout(timer); timer = null; }
      oneTick();
    };
    document.addEventListener('visibilitychange', onVis);

    // --- OPTIONAL: если на бэке есть SSE с событиями по попыткам, подключаемся ---
    // формат события: JSON Attempt в e.data
    try {
      es = new EventSource(`/api/tasks/${taskId}/attempts/stream`, { withCredentials: true });
      es.onmessage = (e) => {
        try {
          const a: Attempt = JSON.parse(e.data);
          setAttempts(prev => {
            const next = mergeAttempts(prev, [a]); // мержим одну
            setSelectedAttempt(curr => (curr && curr.id === a.id ? a : curr));
            savePendingToLS(taskId, next);

            // используем selectedAttempt из замыкания вместо несуществующего sel
            if (a.is_solved && (selectedAttempt?.id === a.id || (prev ?? []).some(x => x.id === a.id))) {
              setCongrats({ coins: a.coins_rewarded ?? 0 });
            }
            return next;
          });
        } catch {}
      };
      es.onerror = () => { es?.close(); es = null; }; // silently fallback на polling
    } catch { /* нет SSE — и ок */ }

    return () => {
      stopped = true;
      if (timer) clearTimeout(timer);
      if (es) es.close();
      document.removeEventListener('visibilitychange', onVis);
    };
  }, [leftTab, taskId]);

  // ====== Helpers ======
  const genDate = (iso: string) => {
    try {
      const d = new Date(iso);
      const day = d.toLocaleString('ru-RU', { day: '2-digit' });
      const month = d.toLocaleString('ru-RU', { month: 'long' }).toLowerCase();
      const time = d.toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      return `${day} ${month} ${time}`;
    } catch {
      return iso;
    }
  };

  // --- attempts utils ---
  function mergeAttempts(prev: Attempt[] | null, incoming: Attempt[]) {
    // incoming — источник истины; но "висящие" из prev не теряем
    const byId = new Map<string, Attempt>();
    incoming.forEach(a => byId.set(a.id, a));
    (prev ?? []).forEach(a => {
      if (!byId.has(a.id) && isAttemptChecking(a)) byId.set(a.id, a);
    });
    return [...byId.values()].sort(
      (a, b) => +new Date(b.created_at) - +new Date(a.created_at)
    );
  }

  // --- pending cache in localStorage (чтобы "Проверка" не пропадала после reload) ---
  function pendingKey(taskId: string) { return `attempts-pending-${taskId}`; }
  const PENDING_TTL_MS = 10 * 60 * 1000; // 10 минут

  function loadPendingFromLS(taskId: string): Attempt[] {
    try {
      const raw = localStorage.getItem(pendingKey(taskId));
      if (!raw) return [];
      const now = Date.now();
      const arr = JSON.parse(raw) as (Attempt & { _cached_at?: number })[];
      return arr.filter(a =>
        isAttemptChecking(a) && (!a._cached_at || now - a._cached_at < PENDING_TTL_MS)
      ).map(({ _cached_at, ...a }) => a);
    } catch { return []; }
  }

  function savePendingToLS(taskId: string, list: Attempt[]) {
    try {
      const toSave = list
        .filter(isAttemptChecking)
        .map(a => ({ ...a, _cached_at: Date.now() }));
      if (toSave.length) localStorage.setItem(pendingKey(taskId), JSON.stringify(toSave));
      else localStorage.removeItem(pendingKey(taskId));
    } catch {}
  }

  // ====== Buy solution ======
  const [buyLoading, setBuyLoading] = useState(false);
  const [boughtSolution, setBoughtSolution] = useState<string | null>(null);
  const buySolution = async () => {
    try {
      setBuyLoading(true);
      setBoughtSolution('');
      const res = await fetchWithAuthOnce(`/api/tasks/${taskId}/solve/stream`, {});
      if (res.status === 402) { setBoughtSolution('Недостаточно монет для покупки решения.'); return; }
      if (!res.ok || !res.body) throw new Error(await res.text().catch(()=> 'HTTP error'));

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      const merge = createStreamMerger('');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const full = merge.push(decoder.decode(value, { stream: true }));
        setBoughtSolution(full); // <-- просто ставим итог
      }
    } catch {
      setBoughtSolution('Не удалось получить решение. Попробуйте позже.');
    } finally {
      setBuyLoading(false);
    }
  };

  // ====== Submit attempt (оптимистично) ======
  async function onSubmit() {
    if (!solution.trim() || submitting) return;
    setSubmitting(true);

    const tempAttempt: Attempt = {
      id: 'temp-' + Date.now(),
      task_id: taskId,
      solution_text: solution,
      feedback: { spans_detail: [] },
      created_at: new Date().toISOString(),
      is_solved: false,
      coins_rewarded: 0,
    };

    // моментально показываем в «Моих посылках»
    setLeftTab('attempts');
    setAttempts((prev) => (prev ? [tempAttempt, ...prev] : [tempAttempt]));
    setSelectedAttempt(tempAttempt);

    try {
      const payload = { task_id: taskId, text: solution };
      const { data } = await api.post<Attempt>('/api/submit', payload);

      setAttempts((prev) => (prev ?? []).map(a => (a.id === tempAttempt.id ? data : a)));
      setSelectedAttempt(data);

      if (data.is_solved) setCongrats({ coins: data.coins_rewarded ?? 0 });
    } finally {
      setSubmitting(false);
    }
  }

  // ====== Extract text from file + DnD ======
  async function onFileChosen(file: File) {
    const fd = new FormData();
    fd.append('file', file);
    const { data } = await api.post<string>('/api/submit/extract_text_from_file', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    if (typeof data === 'string') {
      setSolution(prev => (prev ? (prev + '\n\n' + data) : data));
    }
  }

  // ====== Assistant chat (фикс пропажи сообщений + блокировка на время ответа) ======
  const sendAssistant = async () => {
    const content = assistantInput.trim();
    if (!content || assistantLoading) return;

    const msgs = [...assistantMsgs, { role: 'user', content } as ChatMessage];
    setAssistantMsgs(msgs);
    setAssistantInput('');
    setAssistantLoading(true);

    // Под ассистента — пустой контейнер
    setAssistantMsgs(prev => [...prev, { role: 'assistant', content: '' }]);

    // Аккумулятор, чтобы добавлять только приращение
    const merge = createStreamMerger('');

    try {
      await streamText(
        `/api/tasks/${taskId}/assistant/stream`,          // или teacher/stream
        { messages: msgs },
        (rawChunk) => {
          const full = merge.push(rawChunk);             // <-- получаем ПОЛНЫЙ текст
          setAssistantMsgs(prev => {                     // или setTeacherMsgs
            const copy = prev.slice();
            const last = copy[copy.length - 1];
            if (last?.role === 'assistant') last.content = full; // <-- ставим итог
            return copy;
          });
        },
        { onDone: () => setAssistantLoading(false), onError: () => setAssistantLoading(false) }
      );
    } catch {
      // оставляем, что насобирали
    } finally {
      setAssistantLoading(false);
    }
  };

  const resetAssistant = () => {
    if (assistantLoading) return;
    setAssistantMsgs([]);
    setAssistantInput('');
  };

  // ====== Teacher chat ======
  const startTeacher = async () => {
    if (teacherLockRef.current || teacherLoading) return;
    teacherLockRef.current = true;

    setTeacherLoading(true);
    setTeacherStarted(true);
    // создаём плейсхолдер гарантированно (массив уже есть)
    setTeacherMsgs([{ role: 'assistant', content: '' }]);

    try {
      await streamText(
        `/api/tasks/${taskId}/teacher/init/stream`,
        {},
        (chunk) => {
          // безопасно: не используем prev.slice() вообще
          setTeacherMsgs(curr => {
            const first = curr[0]?.content ?? '';
            const next = [...curr];
            next[0] = { role: 'assistant', content: first + chunk };
            return next;
          });
        },
        {
          onDone: () => { setTeacherLoading(false); teacherLockRef.current = false; },
          onError: () => { setTeacherLoading(false); teacherLockRef.current = false; },
        }
      );
    } catch {
      setTeacherLoading(false);
      teacherLockRef.current = false;
    }
  };

  const sendTeacher = async () => {
    if (!teacherStarted || teacherLoading) return;
    const content = teacherInput.trim();
    if (!content) return;

    // добавляем сообщение пользователя без предположений о prev
    setTeacherMsgs(curr => [...curr, { role: 'user', content }]);
    setTeacherInput('');
    setTeacherLoading(true);

    // плейсхолдер ответа
    setTeacherMsgs(curr => [...curr, { role: 'assistant', content: '' }]);

    const merge = createStreamMerger('');
    try {
      await streamText(
        `/api/tasks/${taskId}/teacher/stream`,
        { messages: [...teacherMsgs, { role: 'user', content }] }, // можно также читать из ref
        (rawChunk) => {
          const idx = rawChunk.indexOf(META_MARK);
          const piece = idx >= 0 ? rawChunk.slice(0, idx) : rawChunk;
          const full = merge.push(piece);

          setTeacherMsgs(curr => {
            if (!curr.length) return [{ role: 'assistant', content: full }];
            const next = [...curr];
            const last = next[next.length - 1];
            next[next.length - 1] =
              last?.role === 'assistant' ? { ...last, content: full } : last;
            return next;
          });

          if (idx >= 0) {
            const metaRaw = rawChunk.slice(idx + META_MARK.length).trim();
            try {
              const meta = JSON.parse(metaRaw);
              if (meta?.type === 'teacher_meta' && meta?.is_solved && meta?.coins_rewarded > 0) {
                setCongrats({ coins: meta.coins_rewarded });
              }
            } catch {}
          }
        },
        { onDone: () => setTeacherLoading(false), onError: () => setTeacherLoading(false) }
      );
    } catch {
      setTeacherLoading(false);
    }
  };

  const resetTeacher = () => {
    if (teacherLoading) return;
    setTeacherMsgs([]);
    setTeacherInput('');
    setTeacherStarted(false);
  };

  if (!task) return null;

  const theme_icon = ICON_BY_THEME_ID[task.theme_id];
  const left = (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Кнопка закрытия (влево к списку задач) */}
      <button
        onClick={() => nav('/app/tasks')}
        className="absolute top-4 left-5 z-50 w-8 h-8 leading-8 text-center bg-white rounded-full text-neutral-900 hover:bg-primary-200"
        aria-label="Закрыть и вернуться к задачам"
      >
        ×
      </button>

      {/* Табы — фиксированы сверху, контент — скроллится отдельно */}
      <div className="flex gap-2 sticky top-0 z-10">
        <TabBtn active={leftTab === 'problem'} onClick={() => setLeftTab('problem')}><b>Задача</b></TabBtn>

        <AnimatePresence initial={false} mode="popLayout">
          {mode === 'solve' && (
            <motion.div
              key="attempts-tab"
              layout
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18 }}
            >
              <TabBtn active={leftTab === 'attempts'} onClick={() => setLeftTab('attempts')}><b>Мои посылки</b></TabBtn>
            </motion.div>
          )}
        </AnimatePresence>

        <TabBtn active={leftTab === 'buy'} onClick={() => setLeftTab('buy')}><b>Решение</b></TabBtn>
      </div>

      <div className="mt-4 flex-1 overflow-auto pr-1">
        {leftTab === 'problem' && (
          <div className="max-w-none">
            {/* Заголовок + тумблер в колонку */}
            <div className="flex flex-col gap-2 mb-4">
              <ModeSwitch mode={mode} onChange={(m) => setMode(m)} />
              <div className="flex items-center gap-3 text-right">
                {theme_icon && <img src={theme_icon} alt="" className="w-[80px] object-contain" />}
                <div className="text-sm text-black">{task.theme_title}</div>
                <div className="text-primary-900 text-xl">{starsByDifficulty(task.difficulty)}</div>
              </div>
              <h2 className="text-2xl font-bold text-black">{task.name}</h2>
            </div>

            {/* Маркдаун с чёрным текстом */}
            <Markdown className="text-black">
              {task.statement_md}
            </Markdown>
          </div>
        )}

        {leftTab === 'attempts' && (
          <AttemptsBlock
            attempts={attempts}
            selected={selectedAttempt}
            onOpen={(a) => setSelectedAttempt(a)}
            onBackToList={() => setSelectedAttempt(null)}
            formatDate={genDate}
          />
        )}

        {leftTab === 'buy' && (
          <BuySolution
            loading={buyLoading}
            onBuy={buySolution}
            text={boughtSolution}
          />
        )}
      </div>
    </div>
  );

  const middle = (
    <EditorBlock
      value={solution}
      onChange={setSolution}
      onFileChosen={onFileChosen}
      onSubmit={onSubmit}
      submitting={submitting}
    />
  );

  const rightAnimated = (
    <AnimatePresence mode="wait" initial={false}>
      {mode === 'solve' ? (
        <motion.div
          key="solve"
          layout
          variants={pane}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={pane.transition}
          className="h-full"
        >
          <AssistantBlock
            messages={assistantMsgs}
            input={assistantInput}
            setInput={setAssistantInput}
            onSend={sendAssistant}
            onReset={resetAssistant}
            loading={assistantLoading}
          />
        </motion.div>
      ) : (
        <motion.div
          key="teach"
          layout
          variants={pane}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={pane.transition}
          className="h-full"
        >
          <TeacherBlock
            messages={teacherMsgs}
            teacherStarted={teacherStarted}
            input={teacherInput}
            setInput={setTeacherInput}
            onSend={sendTeacher}
            onReset={resetTeacher}
            onStart={startTeacher}
            loading={teacherLoading}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <div className="text-white">
      <SolveLayout mode={mode} left={left} middle={middle} right={rightAnimated} />
      {congrats && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white text-neutral-900 rounded-xl2 p-6 w-[420px] text-center">
            <div className="text-2xl font-bold">Поздравляю!</div>
            <div className="mt-2">Задача решена правильно!</div>
            <div className="mt-4 flex items-center justify-center gap-2 text-xl">
              Вы заработали <b>{congrats.coins}</b>
              <img src={ducklar} alt="" className="w-[32px]" />
            </div>
            <div className="mt-6">
              <button onClick={() => setCongrats(null)} className="px-5 py-2 rounded-xl2 bg-primary-500 text-white hover:bg-primary-900 transition">
                Отлично
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- UI ---------- */

function TabBtn({ active, onClick, children }: { active?: boolean; onClick?: () => void; children: React.ReactNode }) {
  return (
    <motion.button
      layout
      onClick={onClick}
      className={
        'px-4 py-2 rounded-t-xl2 transition ' +
        (active ? 'bg-white text-neutral-900' : 'bg-primary-200 text-neutral-800 hover:opacity-90')
      }
      whileTap={{ scale: 0.98 }}
    >
      {children}
    </motion.button>
  );
}

function ModeSwitch({ mode, onChange }: { mode: 'solve'|'teach'; onChange: (m: 'solve'|'teach') => void }) {
  return (
    <div className="flex items-center gap-3 text-neutral-800">
      <span className={mode === 'solve' ? 'font-semibold' : 'opacity-70'}>Режим решения</span>
      <label className="inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          className="sr-only peer"
          checked={mode === 'teach'}
          onChange={(e) => onChange(e.target.checked ? 'teach' : 'solve')}
        />
        <div className="w-12 h-6 bg-gray-200 rounded-full peer-checked:bg-primary-900 relative after:content-[''] after:absolute after:top-[3px] after:left-[3px] after:bg-white after:w-5 after:h-5 after:rounded-full after:transition-all peer-checked:after:translate-x-6" />
      </label>
      <span className={mode === 'teach' ? 'font-semibold' : 'opacity-70'}>Режим преподавания</span>
    </div>
  );
}

/* ---------- Мои посылки ---------- */

function AttemptsBlock({
  attempts, selected, onOpen, onBackToList, formatDate,
}: {
  attempts: Attempt[] | null;
  selected: Attempt | null;
  onOpen: (a: Attempt) => void;
  onBackToList: () => void;
  formatDate: (iso: string) => string;
}) {
  if (!attempts) return <div className="opacity-90">Загрузка попыток…</div>;
  if (attempts.length === 0) return <div className="opacity-90 text-black">Вы ещё не отправляли решение.</div>;

  if (selected) return <AttemptDetails attempt={selected} onBack={onBackToList} />;

  return (
    <div className="space-y-4">
      {attempts.map((a, i) => (
        <div
          key={a.id}
          onClick={() => onOpen(a)}
          className="bg-white rounded-xl2 p-4 border cursor-pointer hover:bg-primary-200/30 transition text-neutral-900"
        >
          <div className="font-semibold">Попытка {attempts.length - i}</div>
          <div className="mt-1 text-sm opacity-90">{mdSnippet(a.solution_text)}</div>

          <div className="mt-2 flex items-center gap-4 text-sm opacity-90">
            <span className="inline-flex items-center gap-2">
              <img src={clockIcon} className="w-4 h-4" alt="" />
              {formatDate(a.created_at)}
            </span>
            <span className="inline-flex items-center gap-2">
              <img src={errorIcon} className="w-4 h-4" alt="" />
              {(a.feedback?.spans_detail?.length ?? 0)} ошибок
            </span>
          </div>

          <div className="mt-2">
            <VerdictBadge attempt={a} />
          </div>
        </div>
      ))}
    </div>
  );
}

function VerdictBadge({ attempt }: { attempt: Attempt }) {
  const isChecking = !attempt.is_solved && (attempt.feedback?.spans_detail?.length ?? 0) === 0;
  if (isChecking) return <span className="inline-block px-3 py-1 rounded-full bg-blue-500 text-white">Проверка</span>;
  if (attempt.is_solved) return <span className="inline-block px-3 py-1 rounded-full bg-green-600 text-white">OK</span>;
  return <span className="opacity-80 inline-block px-3 py-1 rounded-full bg-red-600 text-white">Ошибка решения</span>;
}

function AttemptDetails({ attempt, onBack }: { attempt: Attempt; onBack: () => void }) {
  const spans = attempt.feedback?.spans_detail ?? [];
  const pieces = useMemo(() => highlightPieces(attempt.solution_text ?? '', spans), [attempt, spans]);
  return (
    <div className="text-neutral-900">
      <button onClick={onBack} className="text-primary-900 hover:underline">← Вернуться</button>

      {/* ВЫДЕЛЕНИЕ ТЕКСТА: включено, тултипы не мешают (pointer-events: none) */}
      <div className="mt-3 whitespace-pre-wrap leading-relaxed select-text">
        {pieces.map((p, i) =>
          p.type === 'plain' ? (
            <span key={i}>{p.text}</span>
          ) : (
            <Highlight key={i} text={p.text} message={p.message} />
          )
        )}
      </div>
    </div>
  );
}

/** Хайлайт с «умным» тултипом: если места снизу нет — показываем сверху. */
function Highlight({ text, message }: { text: string; message?: string }) {
  const ref = useRef<HTMLSpanElement | null>(null);
  const [placeTop, setPlaceTop] = useState(false);

  function onEnter() {
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const needTop = r.bottom + 40 > window.innerHeight; // 40 — примерная высота подсказки
    setPlaceTop(needTop);
  }

  return (
    <span
      ref={ref}
      onMouseEnter={onEnter}
      className="relative underline decoration-wavy decoration-red-500 cursor-text group"
    >
      {text}
      {message && (
        <span
          className={
            'absolute left-0 z-10 hidden group-hover:block bg-black text-white text-sm rounded px-2 py-1 max-w-[320px] pointer-events-none ' +
            (placeTop ? 'bottom-full -mb-1' : 'top-full mt-1')
          }
        >
          {message}
        </span>
      )}
    </span>
  );
}

function mdSnippet(s: string, n = 140) {
  const t = (s ?? '').replace(/\s+/g, ' ').trim();
  return t.length > n ? t.slice(0, n - 1) + '…' : t;
}

/* ---------- Покупка решения ---------- */

function BuySolution({ loading, onBuy, text }: { loading: boolean; onBuy: () => void; text: string | null }) {
  return (
    <div className="text-center text-neutral-900">
      {!text && (
        <>
          <div className="text-lg">Вы можете купить просмотр решения этой задачи<br/>за <b>13</b> дакларов</div>
          <button
            disabled={loading}
            onClick={onBuy}
            className="mt-6 flex items-center justify-center gap-2 rounded-xl2 px-6 py-3 font-semibold bg-white border-2 border-primary-500 text-primary-900 hover:bg-primary-200 transition disabled:opacity-70 mx-auto block"
          >
            {loading ? 'Покупаем…' : 'Купить решение 13'}
            <img src={ducklar} alt="" className="w-[32px]" />
          </button>
        </>
      )}
      {text && (
        <div className="text-left bg-white rounded-xl2 p-4 mt-2 border">
          <Markdown className="md">{text}</Markdown>
        </div>
      )}
    </div>
  );
}

/* ---------- Редактор решения (вертикально, DnD) ---------- */

function EditorBlock({
  value, onChange, onFileChosen, onSubmit, submitting,
}: {
  value: string; onChange: (s: string) => void;
  onFileChosen: (f: File) => void;
  onSubmit: () => void;
  submitting: boolean;
}) {
  const dropRef = useRef<HTMLDivElement | null>(null);

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    dropRef.current?.classList.add('ring-2', 'ring-primary-500');
  };
  const onDragLeave = () => {
    dropRef.current?.classList.remove('ring-2', 'ring-primary-500');
  };
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    onDragLeave();
    const file = e.dataTransfer.files?.[0];
    if (file) onFileChosen(file);
  };

  return (
    <div className="h-full flex flex-col text-neutral-900">
      <div className="text-xl font-bold">Решение</div>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Введите решение…"
        className="m-1 flex-1 rounded-xl2 border border-primary-200/60 p-3 outline-none focus:ring-2 focus:ring-primary-500"
      />

      {/* Вертикально: зона для файла -> кнопка «Проверить» */}
      <div
        ref={dropRef}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className="mt-3 rounded-xl2 border-2 border-dashed border-primary-200/80 p-4 text-center bg-primary-100/30"
      >
        <label className="cursor-pointer inline-flex items-center gap-2">
          <input
            type="file"
            accept=".png,.jpg,.jpeg,.pdf,.txt,.md,.tex"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onFileChosen(f);
              e.currentTarget.value = '';
            }}
          />
          <span>Загрузите файл или перетащите сюда (.png, .jpeg, .pdf, .txt, .md, .tex)</span>
        </label>
      </div>

      <button
        onClick={onSubmit}
        disabled={submitting}
        className="mt-3 rounded-xl2 px-6 py-3 bg-primary-500 text-white hover:bg-primary-900 transition disabled:opacity-70"
      >
        {submitting ? 'Проверяем…' : 'Проверить'}
      </button>
    </div>
  );
}

/* ---------- AI помощник (со скроллбаром) ---------- */

/* ---------- AI помощник (Shift+Enter, можно печатать во время ответа, авто-рост textarea) ---------- */

function AssistantBlock({
  messages, input, setInput, onSend, onReset, loading,
}: {
  messages: ChatMessage[];
  input: string;
  setInput: (s: string) => void;
  onSend: () => void;
  onReset: () => void;
  loading: boolean;
}) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const taRef = useRef<HTMLTextAreaElement | null>(null);
  useAutoGrowTextarea(taRef, input, 6); // <-- N = 6 строк

  // автопрокрутка ленты сообщений
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  return (
    <div className="h-full min-h-0 flex flex-col text-neutral-900" aria-busy={loading || undefined} aria-live="polite">
      <div className="flex items-center justify-between sticky top-0 z-10">
        <div className="text-lg font-semibold flex items-center gap-2">
          AI помощник
          {loading && <PulseDot />} {/* ← пульсирующая точка во время генерации */}
        </div>
        <button onClick={onReset} disabled={loading} className="opacity-70 hover:opacity-100 transition disabled:opacity-40">
          <img src={reloadIcon} alt="reload" className="w-6 h-6" />
        </button>
      </div>

      <div className="flex-1 min-h-0 mt-3 bg-white rounded-xl2 border border-primary-200/60 overflow-hidden">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center opacity-90">
            <MascotEyes
              face={mascotFaceWithoutPupils}
              leftEye={{ cxPct: 10, cyPct: 30, radiusPct: 45 }}
              rightEye={{ cxPct: 90, cyPct: 30, radiusPct: 45 }}
              pupilSize={30}
              pupilColor="white"
              className="mx-auto w-[200px] mb-6 pointer-events-none"
            />
            <div className="mt-3 text-center px-3">
              Застрял? Спроси у меня подсказку и я тебе помогу!
            </div>
          </div>
        ) : (
          <div ref={scrollRef} className="p-3 space-y-3 overflow-y-auto h-full [scrollbar-gutter:stable]">
            {messages.map((m, i) => (
              <div
                key={i}
                className={'group ' + (m.role === 'user' ? 'text-right' : 'text-left')}
              >
                <div
                  className={
                    'relative inline-block max-w-[80%] rounded-xl2 px-3 py-2 ' +
                    (m.role === 'user' ? 'bg-primary-500 text-white' : 'bg-primary-100')
                  }
                >
                  {/* Кнопка копирования — только для ответов ассистента */}
                  {m.role !== 'user' && (
                    <CopyButton
                      text={m.content}
                      className="absolute top-1.5 right-1.5 opacity-0 group-hover:opacity-100 focus:opacity-100"
                      label="Скопировать ответ"
                    />
                  )}
                  <Markdown className="md">{m.content}</Markdown>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-end gap-2">
        <textarea
          ref={taRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}         // ← можно печатать всегда
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              if (e.shiftKey) return;                        // Shift+Enter = перенос строки
              e.preventDefault();
              if (!loading) onSend();                        // во время ответа отправка запрещена
            }
          }}
          placeholder="Shift+Enter — перенос строки"
          className="flex-1 rounded-xl2 px-4 py-3 bg-primary-900/10 outline-none
                     disabled:opacity-60 resize-none leading-6"
          // НЕ отключаем textarea при loading — сохраняем фокус
        />
        <button
          onClick={onSend}
          disabled={loading || !input.trim()}
          className="p-3 rounded-xl2 hover:bg-primary-900/10 transition disabled:opacity-40 inline-flex items-center"
          aria-disabled={loading}
          title={loading ? 'Модель печатает… отправка недоступна' : 'Отправить'}
        >
          <img src={sendIcon} alt="send" className="w-7 h-7" />
          {loading && <PulseDot className="ml-2" />} {/* ← точка на кнопке */}
        </button>
      </div>
    </div>
  );
}

/* ---------- AI учитель ---------- */

function TeacherBlock({
  messages, teacherStarted, input, setInput, onSend, onReset, onStart, loading,
}: {
  messages: ChatMessage[];
  teacherStarted: boolean;
  input: string;
  setInput: (s: string) => void;
  onSend: () => void;
  onReset: () => void;
  onStart: () => void;
  loading: boolean;
}) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const taRef = useRef<HTMLTextAreaElement | null>(null);
  useAutoGrowTextarea(taRef, input, 6); // <-- N = 6 строк

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  return (
    <div className="h-full min-h-0 flex flex-col text-neutral-900" aria-busy={loading || undefined} aria-live="polite">
      <div className="flex items-center justify-between sticky top-0 z-10">
        <div className="text-lg font-semibold flex items-center gap-2">
          AI учитель
          {loading && <PulseDot />}  {/* ← точка */}
        </div>
        <button onClick={onReset} disabled={loading} className="opacity-70 hover:opacity-100 transition disabled:opacity-40">
          <img src={reloadIcon} alt="reload" className="w-6 h-6" />
        </button>
      </div>

      <div className="flex-1 min-h-0 mt-3 bg-white rounded-xl2 border border-primary-200/60 overflow-hidden">
        {!teacherStarted ? (
          <div className="h-full flex flex-col items-center justify-center gap-3">
            <MascotEyes
              face={mascotFaceWithoutPupils}
              leftEye={{ cxPct: 10, cyPct: 30, radiusPct: 45 }}
              rightEye={{ cxPct: 90, cyPct: 30, radiusPct: 45 }}
              pupilSize={30}
              pupilColor="white"
              className="mx-auto w-[200px] mb-6 pointer-events-none"
            />
            <div className="mt-3 text-center px-3">
              Давай начнем вместе по шагам решать задачу!<br></br>Запусти режим преподавания
            </div>
            <Button
              onClick={onStart}
              disabled={loading}
              className="bg-primary-500"
            >
              Запустить
            </Button>
          </div>
        ) : (
          <div ref={scrollRef} className="p-3 space-y-3 overflow-y-auto h-full [scrollbar-gutter:stable]">
            {messages.map((m, i) => (
              <div
                key={i}
                className={'group ' + (m.role === 'user' ? 'text-right' : 'text-left')}
              >
                <div
                  className={
                    'relative inline-block max-w-[80%] rounded-xl2 px-3 py-2 ' +
                    (m.role === 'user' ? 'bg-primary-500 text-white' : 'bg-primary-100')
                  }
                >
                  {m.role !== 'user' && (
                    <CopyButton
                      text={m.content}
                      className="absolute top-1.5 right-1.5 opacity-0 group-hover:opacity-100 focus:opacity-100"
                      label="Скопировать ответ"
                    />
                  )}
                  <Markdown className="md">{m.content}</Markdown>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {teacherStarted && (
        <div className="mt-3 flex items-end gap-2">
          <textarea
            ref={taRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}       // ← можно печатать всегда
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                if (e.shiftKey) return;                      // Shift+Enter = перенос строки
                e.preventDefault();
                if (!loading) onSend();                      // во время ответа отправка запрещена
              }
            }}
            placeholder="Shift+Enter — перенос строки"
            className="flex-1 rounded-xl2 px-4 py-3 bg-primary-900/10 outline-none
                       disabled:opacity-60 resize-none leading-6"
          />
          <button
            onClick={onSend}
            disabled={loading || !input.trim()}
            className="p-3 rounded-xl2 hover:bg-primary-900/10 transition disabled:opacity-40 inline-flex items-center"
            aria-disabled={loading}
            title={loading ? 'Модель печатает… отправка недоступна' : 'Отправить'}
          >
            <img src={sendIcon} alt="send" className="w-7 h-7" />
            {loading && <PulseDot className="ml-2" />}
          </button>
        </div>
      )}
    </div>
  );
}


/* ---------- подсветка текста ---------- */

function highlightPieces(text: string, spans: Span[]) {
  const res: Array<{ type: 'plain'|'highlight'; text: string; message?: string }> = [];
  let idx = 0;
  const sorted = (spans ?? []).slice().sort((a, b) => a.start - b.start);
  for (const s of sorted) {
    const a = Math.max(0, Math.min(text.length, s.start));
    const b = Math.max(0, Math.min(text.length, s.end));
    if (a > idx) res.push({ type: 'plain', text: text.slice(idx, a) });
    res.push({ type: 'highlight', text: text.slice(a, b), message: s.message });
    idx = b;
  }
  if (idx < text.length) res.push({ type: 'plain', text: text.slice(idx) });
  return res;
}

/* ---------- хелперы ---------- */
function useAutoGrowTextarea(
  ref: React.RefObject<HTMLTextAreaElement>,
  value: string,
  maxRows = 6
) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const cs = window.getComputedStyle(el);
    // fallback для 'normal'
    const lineHeight =
      parseFloat(cs.lineHeight) || (parseFloat(cs.fontSize || '16') * 1.5) || 24;
    const paddingTop = parseFloat(cs.paddingTop || '0');
    const paddingBottom = parseFloat(cs.paddingBottom || '0');
    const maxHeight = lineHeight * maxRows + paddingTop + paddingBottom;

    el.style.height = 'auto';
    const newH = Math.min(el.scrollHeight, maxHeight);
    el.style.height = newH + 'px';
    el.style.overflowY = el.scrollHeight > newH ? 'auto' : 'hidden';
  }, [ref, value, maxRows]);
}

function PulseDot({ className = '', title = 'Генерирую…' }: { className?: string; title?: string }) {
  return (
    <span
      className={`inline-block w-2.5 h-2.5 rounded-full bg-primary-500 animate-pulse ${className}`}
      aria-label={title}
      title={title}
    />
  );
}

const isAttemptChecking = (a: Attempt) =>
  !a.is_solved && ((a.feedback?.spans_detail?.length ?? 0) === 0);

function starsByDifficulty(d: Difficulty) {
  const s = d === 'easy' ? 1 : d === 'medium' ? 2 : 3;
  return '★'.repeat(s) + '☆'.repeat(3 - s);
}