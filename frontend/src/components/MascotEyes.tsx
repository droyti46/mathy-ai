import { useEffect, useRef, useState } from "react";

type Eye = { cxPct: number; cyPct: number; radiusPct: number };

interface MascotEyesProps {
  face: string;
  leftEye: Eye;
  rightEye: Eye;
  pupilSize?: number;
  pupilColor?: string;
  className?: string;
}

/**
 * Компонент "умных глаз" уточки Мати.
 * Зрачки следят за курсором мыши, но не выходят за пределы "глаза".
 */
export default function MascotEyes({
  face,
  leftEye,
  rightEye,
  pupilSize = 24,
  pupilColor = "#000",
  className = "",
}: MascotEyesProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [offsets, setOffsets] = useState<{ L: [number, number]; R: [number, number] }>({
    L: [0, 0],
    R: [0, 0],
  });

  useEffect(() => {
  const el = ref.current!;
  if (!el) return;

  const onMove = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect();
      // курсор в координатах контейнера
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      const calc = (eye: Eye) => {
      const cx = (eye.cxPct / 100) * rect.width;
      const cy = (eye.cyPct / 100) * rect.height;
      const maxR = (eye.radiusPct / 100) * Math.min(rect.width, rect.height) * 0.35;

      let dx = mx - cx;
      let dy = my - cy;
      const len = Math.hypot(dx, dy) || 1;
      const k = Math.min(maxR / len, 1); // 👈 кламп: дальше радиуса не идём
      return [dx * k, dy * k] as [number, number];
      };

      setOffsets({ L: calc(leftEye), R: calc(rightEye) });
  };

  window.addEventListener("mousemove", onMove); // 👈 глобально
  return () => window.removeEventListener("mousemove", onMove);
  }, [leftEye, rightEye]);

  return (
    <div ref={ref} className={`relative select-none ${className}`}>
      <img src={face} alt="Мати" className="w-full block" />

      <Pupil eye={leftEye} offset={offsets.L} size={pupilSize} color={pupilColor} />
      <Pupil eye={rightEye} offset={offsets.R} size={pupilSize} color={pupilColor} />
    </div>
  );
}

function Pupil({
  eye,
  offset,
  size,
  color = "#000", // 👈 новый параметр
}: {
  eye: Eye;
  offset: [number, number];
  size: number;
  color?: string;
}) {
  return (
    <div
      className="absolute"
      style={{
        left: `${eye.cxPct}%`,
        top: `${eye.cyPct}%`,
        transform: `translate(calc(-50% + ${offset[0]}px), calc(-50% + ${offset[1]}px))`,
      }}
    >
      <div
        className="rounded-full"
        style={{ width: size, height: size, backgroundColor: color }} // 👈 цвет зрачка
      />
    </div>
  );
}

