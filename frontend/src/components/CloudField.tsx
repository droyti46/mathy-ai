import { useEffect, useMemo, useRef, useState } from 'react';

type Sprite = string;
type Cloud = { id: number; sprite: Sprite; top: string; s: number; dur: number };

function rand(min: number, max: number) {
  return Math.random() * (max - min) + min;
}

export default function CloudField({ sprites, density = 4 }: { sprites: Sprite[]; density?: number }) {
  const idRef = useRef(0);
  const [clouds, setClouds] = useState<Cloud[]>([]);

  const make = () => ({
    id: ++idRef.current,
    sprite: sprites[Math.floor(Math.random() * sprites.length)],
    top: `${rand(8, 70)}%`,
    s: rand(0.8, 1.25),
    dur: rand(22, 38) // секунды
  });

  // начальная партия
  useEffect(() => {
    setClouds(Array.from({ length: density }, make));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {clouds.map((c) => (
        <img
          key={c.id}
          src={c.sprite}
          className="maty-cloud"
          style={
            {
              // кастомные CSS-переменные для анимации
              ['--top' as any]: c.top,
              ['--s' as any]: c.s,
              ['--dur' as any]: `${c.dur}s`
            } as React.CSSProperties
          }
          onAnimationEnd={() => {
            // как только облако ушло вправо — убираем и сразу спауним новое слева
            setClouds((prev) => prev.filter((x) => x.id !== c.id).concat(make()));
          }}
          alt=""
        />
      ))}
    </div>
  );
}
