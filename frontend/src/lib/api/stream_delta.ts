// БЕЗОПАСНО: убираем только \r, чтобы не ломать математику/пробелы.
const norm = (s: string) => s.replace(/\r/g, '');

/**
 * На каждом chunk возвращает ПОЛНЫЙ слитый текст (идемпотентно).
 * Работает и с "дельтами", и с "накопительными" кусками, и с повторами.
 */
export function createStreamMerger(initial = '') {
  let acc = initial;

  function push(rawChunk: string): string {
    if (!rawChunk) return acc;

    const a = acc;
    const b = rawChunk;
    const an = norm(a);
    const bn = norm(b);

    // Полный повтор в нормализованном виде — ничего не меняем
    if (bn === an) return acc;

    // Найдём наибольший t: norm(a.slice(a.len - t)) === norm(b.slice(0, t))
    const max = Math.min(a.length, b.length);
    let t = max;
    while (t > 0) {
      if (norm(a.slice(a.length - t)) === norm(b.slice(0, t))) break;
      t--;
    }

    if (t > 0) {
      // есть перекрытие по границе — добавляем только "хвост" b
      acc = a + b.slice(t);
      return acc;
    }

    // Нет перекрытия на границе. Часто это "накопительный" b (b содержит весь a).
    // В таком случае просто берём b, чтобы избежать удвоений.
    if (bn.startsWith(an)) {
      acc = b;
      return acc;
    }

    // Иначе считаем, что это независимый фрагмент (редко) — конкатим как есть.
    acc = a + b;
    return acc;
  }

  return {
    /** Текущее слитое значение */
    value: () => acc,
    /** Принять новый чанк и вернуть ПОЛНЫЙ итоговый текст */
    push,
    /** Сбросить */
    reset: (v = '') => { acc = v; },
  };
}
