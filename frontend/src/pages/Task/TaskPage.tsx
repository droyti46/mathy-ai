import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '@/lib/api/axios';
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
  const [teacherMsgs, setTeacherMsgs] = useState<ChatMessage[] | null>(null);
  const [teacherInput, setTeacherInput] = useState('');
  const [teacherLoading, setTeacherLoading] = useState(false);

  // ====== Congrats modal ======
  const [congrats, setCongrats] = useState<{ coins: number } | null>(null);

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

  // Ленивая загрузка попыток
  useEffect(() => {
    if (leftTab !== 'attempts' || !taskId) return;
    (async () => {
      const { data } = await api.get<Attempt[]>(`/api/tasks/${taskId}/attempts`);
      setAttempts(data);
      setSelectedAttempt(null);
    })();
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

  // ====== Buy solution ======
  const [buyLoading, setBuyLoading] = useState(false);
  const [boughtSolution, setBoughtSolution] = useState<string | null>(null);
  const buySolution = async () => {
    try {
      setBuyLoading(true);
      const { data } = await api.post<ChatOut>(`/api/tasks/${taskId}/solve`);
      const text = (data.messages ?? []).map(m => m.content).join('\n\n');
      setBoughtSolution(text || 'Решение получено.');
    } catch (e: any) {
      if (e?.response?.status === 402) {
        setBoughtSolution('Недостаточно монет для покупки решения.');
      } else {
        setBoughtSolution('Не удалось получить решение. Попробуйте позже.');
      }
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

    try {
      const { data } = await api.post<ChatOut>(`/api/tasks/${taskId}/assistant`, { messages: msgs });
      const srv = data?.messages ?? [];

      // 1) Если сервер вернул всю историю (должно быть больше, чем локально отправили — т.е. плюс ответ ассистента)
      if (srv.length > msgs.length) {
        setAssistantMsgs(srv);
        return;
      }

      // 2) Иначе сервер прислал только последний ответ ассистента — аккуратно добавим его в хвост
      const assistantReply = srv.find(m => m.role === 'assistant');
      if (assistantReply) {
        setAssistantMsgs(prev => {
          const last = prev[prev.length - 1];
          // простая защита от дублей по роли+контенту
          if (last?.role === 'assistant' && last?.content === assistantReply.content) return prev;
          return [...prev, assistantReply];
        });
      }
      // если вообще ничего не пришло — оставляем локальную историю как есть
    } catch {
      // опционально показать тост об ошибке
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
    if (teacherLoading) return;
    setTeacherLoading(true);
    try {
      const { data } = await api.post<ChatOut>(`/api/tasks/${taskId}/teacher/init`);
      setTeacherMsgs(data.messages);
    } finally {
      setTeacherLoading(false);
    }
  };
  const sendTeacher = async () => {
    if (!teacherMsgs || teacherLoading) return;
    const content = teacherInput.trim();
    if (!content) return;

    const msgs = [...teacherMsgs, { role: 'user', content } as ChatMessage];
    setTeacherMsgs(msgs);
    setTeacherInput('');
    setTeacherLoading(true);
    try {
      const { data } = await api.post<TeacherOut>(`/api/tasks/${taskId}/teacher`, { messages: msgs });
      setTeacherMsgs(data.messages);
      if (data.is_solved) setCongrats({ coins: data.coins_rewarded ?? 0 });
    } finally {
      setTeacherLoading(false);
    }
  };
  const resetTeacher = () => {
    if (teacherLoading) return;
    setTeacherMsgs(null);
    setTeacherInput('');
  };

  if (!task) return null;

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
        <TabBtn active={leftTab === 'problem'} onClick={() => setLeftTab('problem')}>Задача</TabBtn>
        {mode === 'solve' && <TabBtn active={leftTab === 'attempts'} onClick={() => setLeftTab('attempts')}>Мои посылки</TabBtn>}
        <TabBtn active={leftTab === 'buy'} onClick={() => setLeftTab('buy')}>Решение</TabBtn>
      </div>

      <div className="mt-4 flex-1 overflow-auto pr-1">
        {leftTab === 'problem' && (
          <div className="max-w-none">
            {/* Заголовок + тумблер в колонку */}
            <div className="flex flex-col gap-2 mb-4">
              <ModeSwitch mode={mode} onChange={(m) => setMode(m)} />
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

  const right = mode === 'solve'
    ? <AssistantBlock
        messages={assistantMsgs}
        input={assistantInput}
        setInput={setAssistantInput}
        onSend={sendAssistant}
        onReset={resetAssistant}
        loading={assistantLoading}
      />
    : <TeacherBlock
        messages={teacherMsgs}
        input={teacherInput}
        setInput={setTeacherInput}
        onSend={sendTeacher}
        onReset={resetTeacher}
        onStart={startTeacher}
        loading={teacherLoading}
      />;

  return (
    <div className="text-white">
      <SolveLayout mode={mode} left={left} middle={middle} right={right} />
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
    <button
      onClick={onClick}
      className={
        'px-4 py-2 rounded-t-xl2 transition ' +
        (active ? 'bg-white text-neutral-900' : 'bg-primary-200 text-neutral-800 hover:opacity-90')
      }
    >
      {children}
    </button>
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
  if (attempts.length === 0) return <div className="opacity-90">Вы ещё не отправляли решение.</div>;

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
  return <span className="inline-block px-3 py-1 rounded-full bg-red-600 text-white">Ошибка решения</span>;
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
            className="mt-6 rounded-xl2 px-6 py-3 font-semibold bg-white border-2 border-primary-500 text-primary-900 hover:bg-primary-200 transition disabled:opacity-70"
          >
            {loading ? 'Покупаем…' : 'Купить решение 13 🪙'}
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
        className="mt-3 flex-1 rounded-xl2 border border-primary-200/60 p-3 outline-none focus:ring-2 focus:ring-primary-500"
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

/* ---------- AI помощник (фикс истории + блокировка) ---------- */

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
  return (
    <div className="h-full flex flex-col text-neutral-900">
      <div className="flex items-center justify-between sticky top-0 z-10">
        <div className="text-lg font-semibold">AI помощник</div>
        <button onClick={onReset} disabled={loading} className="opacity-70 hover:opacity-100 transition disabled:opacity-40">
          <img src={reloadIcon} alt="reload" className="w-6 h-6" />
        </button>
      </div>

      <div className="flex-1 mt-3 bg-white rounded-xl2 border border-primary-200/60">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center opacity-90">
            <MascotEyes
              face={mascotFaceWithoutPupils}
              leftEye={{ cxPct: 10, cyPct: 30, radiusPct: 45 }}
              rightEye={{ cxPct: 90, cyPct: 30, radiusPct: 45 }}
              pupilSize={30}
              pupilColor='white'
              className="mx-auto w-[200px] mb-6 pointer-events-none"
            />
            <div className="mt-3 text-center px-3">
              Застрял? Спроси у меня подсказку и я тебе помогу!
            </div>
          </div>
        ) : (
          <div className="p-3 space-y-3 overflow-auto h-full">
            {messages.map((m, i) => (
              <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
                <div className={'inline-block max-w-[80%] rounded-xl2 px-3 py-2 ' + (m.role === 'user' ? 'bg-primary-500 text-white' : 'bg-primary-100')}>
                  <Markdown className="md">{m.content}</Markdown>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => (!loading && e.key === 'Enter' ? onSend() : undefined)}
          disabled={loading}
          placeholder="Shift+Enter, чтобы вставить пустую строку"
          className="flex-1 rounded-xl2 px-4 py-3 bg-primary-900/10 outline-none disabled:opacity-60"
        />
        <button onClick={onSend} disabled={loading} className="p-3 rounded-xl2 hover:bg-primary-900/10 transition disabled:opacity-40">
          <img src={sendIcon} alt="send" className="w-7 h-7" />
        </button>
      </div>
    </div>
  );
}

/* ---------- AI учитель ---------- */

function TeacherBlock({
  messages, input, setInput, onSend, onReset, onStart, loading,
}: {
  messages: ChatMessage[] | null;
  input: string;
  setInput: (s: string) => void;
  onSend: () => void;
  onReset: () => void;
  onStart: () => void;
  loading: boolean;
}) {
  return (
    <div className="h-full flex flex-col text-neutral-900">
      <div className="flex items-center justify-between sticky top-0 z-10">
        <div className="text-lg font-semibold">AI учитель</div>
        <button onClick={onReset} disabled={loading} className="opacity-70 hover:opacity-100 transition disabled:opacity-40">
          <img src={reloadIcon} alt="reload" className="w-6 h-6" />
        </button>
      </div>

      <div className="flex-1 mt-3 bg-white rounded-xl2 border border-primary-200/60">
        {messages === null ? (
          <div className="h-full flex flex-col items-center justify-center">
            <button
              onClick={onStart}
              disabled={loading}
              className="rounded-xl2 px-6 py-3 bg-primary-500 text-white hover:bg-primary-900 transition disabled:opacity-60"
            >
              Запустить
            </button>
          </div>
        ) : (
          <div className="p-3 space-y-3 overflow-auto h-full">
            {messages.map((m, i) => (
              <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
                <div className={'inline-block max-w-[80%] rounded-xl2 px-3 py-2 ' + (m.role === 'user' ? 'bg-primary-500 text-white' : 'bg-primary-100')}>
                  <Markdown className="md">{m.content}</Markdown>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {messages && (
        <div className="mt-3 flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => (!loading && e.key === 'Enter' ? onSend() : undefined)}
            disabled={loading}
            placeholder="Shift+Enter, чтобы вставить пустую строку"
            className="flex-1 rounded-xl2 px-4 py-3 bg-primary-900/10 outline-none disabled:opacity-60"
          />
          <button onClick={onSend} disabled={loading} className="p-3 rounded-xl2 hover:bg-primary-900/10 transition disabled:opacity-40">
            <img src={sendIcon} alt="send" className="w-7 h-7" />
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
