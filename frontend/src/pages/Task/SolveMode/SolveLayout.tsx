import { useEffect, useRef, useState } from 'react';

type Props = {
  mode: 'solve' | 'teach';
  left: React.ReactNode;
  middle?: React.ReactNode;
  right: React.ReactNode;
};

/**
 * Сплит-лейаут с перетаскиваемыми разделителями.
 * В режиме «решение» — 3 панели, в «преподавание» — 2 панели.
 * Заполняет весь экран, внутри — белые карточки с отступами.
 */
export default function SolveLayout({ mode, left, middle, right }: Props) {
  const isTeach = mode === 'teach';
  const ref = useRef<HTMLDivElement | null>(null);

  const [w1, setW1] = useState(34);
  const [w2, setW2] = useState(33);
  const [w3, setW3] = useState(33);

  useEffect(() => {
    if (isTeach) { setW1(50); setW3(50); }
    else { setW1(33); setW2(34); setW3(33); }
  }, [isTeach]);

  function startDrag(which: 'a'|'b') {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();

    const onMove = (e: PointerEvent) => {
      const x = e.clientX - rect.left;
      const pct = (x / rect.width) * 100;

      if (isTeach) {
        const clamped = Math.max(20, Math.min(80, pct));
        setW1(clamped); setW3(100 - clamped);
      } else if (which === 'a') {
        const clamped = Math.max(15, Math.min(70, pct));
        const rest = 100 - clamped;
        const w2n = Math.max(15, Math.min(rest - 15, w2));
        setW1(clamped); setW2(w2n); setW3(100 - clamped - w2n);
      } else {
        const left = w1;
        const total23 = 100 - left;
        const pct23 = (pct - left) / total23 * (w2 + w3);
        const p2 = Math.max(15, Math.min(w2 + w3 - 15, pct23));
        setW2(p2); setW3(w2 + w3 - p2);
      }
    };
    const onUp = () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  }

  return (
    <div className="fixed inset-0 bg-primary-500">
      <div ref={ref} className="h-full w-full flex p-3 gap-3">
        {/* Left */}
        <section style={{ width: `${w1}%` }} className="h-full bg-white rounded-xl2 p-4 overflow-hidden">
          <div className="h-full overflow-hidden">{left}</div>
        </section>

        {/* Handle A */}
        <div
          role="separator"
          onPointerDown={() => startDrag('a')}
          className="w-2 cursor-col-resize group"
          aria-orientation="vertical"
          title="Перетащите, чтобы изменить ширину"
        >
          <div className="h-full mx-auto w-[3px] bg-primary-200 group-hover:bg-primary-500 transition rounded" />
        </div>

        {/* Middle (нет в teach) */}
        {!isTeach && (
          <>
            <section style={{ width: `${w2}%` }} className="h-full bg-white rounded-xl2 p-4 overflow-hidden">
              <div className="h-full overflow-hidden">{middle}</div>
            </section>

            {/* Handle B */}
            <div
              role="separator"
              onPointerDown={() => startDrag('b')}
              className="w-2 cursor-col-resize group"
              aria-orientation="vertical"
              title="Перетащите, чтобы изменить ширину"
            >
              <div className="h-full mx-auto w-[3px] bg-primary-200 group-hover:bg-primary-500 transition rounded" />
            </div>
          </>
        )}

        {/* Right */}
        <section style={{ width: `${w3}%` }} className="h-full bg-white rounded-xl2 p-4 overflow-hidden">
          <div className="h-full overflow-hidden">{right}</div>
        </section>
      </div>
    </div>
  );
}
