from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any

import pandas as pd
import re


@dataclass(frozen=True)
class TheoryId:
    theme_id: str
    lesson_id: str
    theme_title: str


@dataclass
class TheoryLesson:
    theme_id: str
    lesson_id: str
    title: str
    section_title: str
    prompt: Optional[str]
    answer_md: str


class PandasTheoryRepo:
    """
    Простое read-only хранилище теории из CSV.
    Ожидаемые колонки CSV (рус.):
      - 'Раздел'         -> название раздела (theme title)
      - '№ темы'         -> номер/идентификатор урока в разделе
      - 'Тема'           -> заголовок урока
      - 'Prompt'         -> (опц.) исходный prompt
      - 'Ответ'          -> Markdown/текст теории
      - 'OK', 'Ошибка'   -> (игнорируются здесь)
    """

    def __init__(self, data_dir: str | Path, filename: str = "theory.csv") -> None:
        self._csv_path = data_dir
        self._df = self._load()

    # ---------- public API ----------

    def list_all_ids(self) -> List[TheoryId]:
        """Список всех пар (theme_id, lesson_id) для фронта."""
        return [
            TheoryId(
                theme_id=row["theme_id"],
                lesson_id=row["lesson_id"],
                theme_title=row["section"],  # ← берём из колонки «Раздел»
            )
            for _, row in self._df.iterrows()
        ]

    def list_tree(self) -> List[Dict[str, Any]]:
        """
        Дерево тем с уроками:
        [
          {
            "id": theme_id, "title": section_title,
            "lessons": [{"id": lesson_id, "title": title}, ...]
          },
          ...
        ]
        """
        out: List[Dict[str, Any]] = []
        for theme_id, g in self._df.groupby("theme_id", sort=True):
            section_title: str = g["section"].iloc[0]
            lessons = [
                {"id": r["lesson_id"], "title": r["title"]}
                for _, r in g.sort_values(["lesson_order", "lesson_id"]).iterrows()
            ]
            out.append({"id": theme_id, "title": section_title, "lessons": lessons})
        out.sort(key=lambda x: x["title"])
        return out

    def get_lesson(self, theme_id: str, lesson_id: str) -> Optional[TheoryLesson]:
        """Найти урок по паре id."""
        m = self._df[
            (self._df["theme_id"] == theme_id) & (self._df["lesson_id"] == lesson_id)
        ]
        if m.empty:
            return None
        r = m.iloc[0]
        return TheoryLesson(
            theme_id=r["theme_id"],
            lesson_id=r["lesson_id"],
            title=r["title"],
            section_title=r["section"],
            prompt=r.get("prompt") or None,
            answer_md=r.get("answer_md") or "# Пусто\nМатериал для этого урока пока не добавлен.",
        )

    # ---------- internals ----------

    @staticmethod
    def _slugify(value: Any) -> str:
        s = str(value).strip().lower()
        # замена пробелов и разделителей на тире
        s = re.sub(r"[ \t+/._]+", "-", s)
        # русские/латинские буквы и цифры, остальное убрать
        s = re.sub(r"[^a-z0-9\-а-яё]", "", s)
        # транслитерация простая, чтобы ID были «стабильные»
        # (минимально: ё->e, ъ/ь удаляем)
        repl = {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
            "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
            "й": "j", "к": "k", "л": "l", "м": "m", "н": "n",
            "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
            "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "ch",
            "ш": "sh", "щ": "sch", "ы": "y", "э": "e", "ю": "yu",
            "я": "ya", "ь": "", "ъ": "",
        }
        s = "".join(repl.get(ch, ch) for ch in s)
        s = re.sub(r"-{2,}", "-", s).strip("-")
        return s or "id"

    def _load(self) -> pd.DataFrame:
        if not self._csv_path.exists():
            raise FileNotFoundError(f"theory csv not found at: {self._csv_path}")

        df = pd.read_csv(self._csv_path, encoding="utf-8-sig")

        # Нормализуем русские заголовки → английские ключи
        colmap = {
            "Раздел": "section",
            "№ темы": "lesson_no",
            "Тема": "title",
            "Prompt": "prompt",
            "Ответ": "answer_md",
            "OK": "ok",
            "Ошибка": "err",
        }
        # поддержка разных регистров/пробелов
        rename = {}
        for c in df.columns:
            cc = c.strip()
            rename[c] = colmap.get(cc, cc)
        df = df.rename(columns=rename)

        # Базовая валидация
        for need in ["section", "title"]:
            if need not in df.columns:
                raise ValueError(f"Column '{need}' is required in theory csv")

        if "lesson_no" not in df.columns:
            df["lesson_no"] = range(1, len(df) + 1)

        # theme_id = slug(section)
        df["theme_id"] = df["section"].apply(self._slugify)

        # lesson_id: если lesson_no число — используем с нулями, иначе слаг от title
        def make_lesson_id(row) -> str:
            val = row.get("lesson_no")
            if pd.notna(val):
                try:
                    n = int(val)
                    return f"{n:03d}"
                except Exception:
                    pass
            return self._slugify(row.get("title", "lesson"))

        df["lesson_id"] = df.apply(make_lesson_id, axis=1)

        # Для предсказуемой сортировки
        def lesson_order(row) -> int:
            try:
                return int(row.get("lesson_no"))
            except Exception:
                return 10_000  # текстовые номера уходят в конец

        df["lesson_order"] = df.apply(lesson_order, axis=1)

        # Заполним отсутствующие поля
        if "answer_md" not in df.columns:
            df["answer_md"] = ""
        if "prompt" not in df.columns:
            df["prompt"] = None

        # Убираем полностью пустые строки по ключевым полям
        df = df.dropna(subset=["section", "title"]).reset_index(drop=True)

        return df
