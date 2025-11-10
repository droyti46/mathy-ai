from __future__ import annotations

import datetime
import re
from collections import Counter
from typing import Optional

import pandas as pd

from app.domain.tasks.entities import Task
from app.core.attempts import is_attempt_solved


class PandasTaskRepo:
    @staticmethod
    def _slugify(value: str, default: str) -> str:
        value = str(value).strip().lower()
        if not value:
            return default
        value = re.sub(r"\s+", "-", value)
        value = re.sub(r"[^0-9a-zA-Zа-яА-Я-]", "-", value)
        value = re.sub(r"-+", "-", value).strip("-")
        return value or default

    def __init__(self, path: str):
        self.path = path
        df = pd.read_csv(path)

        columns_lower = {str(c).strip().lower(): c for c in df.columns}

        def pick(*names: str) -> Optional[str]:
            for n in names:
                key = n.strip().lower()
                if key in columns_lower:
                    return columns_lower[key]
            return None

        def ensure_column(name: str, source_names: list[str], default: str = ""):
            if name in df.columns:
                return
            src = pick(name, *source_names)
            if src:
                df[name] = df[src]
            else:
                df[name] = default

        ensure_column("statement_md", ["statement", "task", "текст", "условие"], "")
        ensure_column("reference_solution_md", ["solution", "reference_solution", "решение"], "")
        ensure_column("theme_id", ["theme", "тема"], "math")
        ensure_column("difficulty", ["уровень сложности", "сложность", "level"], "easy")
        ensure_column("name", ["Название"], "Задача")
        ensure_column("source", [], "")
        ensure_column("tags", [], "")

        diff_map = {
            "легкий": "easy",
            "лёгкий": "easy",
            "easy": "easy",
            "простой": "easy",
            "medium": "medium",
            "средний": "medium",
            "нормальный": "medium",
            "сложный": "hard",
            "hard": "hard",
            "тяжелый": "hard",
            "тяжёлый": "hard",
        }

        def normalize_difficulty(value):
            if value is None or value == "":
                return "easy"
            return diff_map.get(str(value).strip().lower(), "medium")

        df["statement_md"] = df["statement_md"].fillna("").astype(str)
        df["reference_solution_md"] = df["reference_solution_md"].fillna("").astype(str)
        df["theme_id"] = df["theme_id"].fillna("math").astype(str)
        df["difficulty"] = df["difficulty"].apply(normalize_difficulty)
        if "id" not in df.columns:
            df["id"] = df.index.astype(str)

        # detect lesson columns after ensuring required fields
        columns_lower = {str(c).strip().lower(): c for c in df.columns}

        def pick_column(*names: str) -> Optional[str]:
            for n in names:
                key = n.strip().lower()
                if key in columns_lower:
                    return columns_lower[key]
            return None

        lesson_id_col = pick_column("lesson_id", "lesson key", "lesson_code", "lesson_slug", "lesson")
        lesson_title_col = pick_column(
            "lesson_title",
            "lesson_name",
            "lesson",
            "подтема",
            "подтема",
            "урок",
            "subtheme",
            "unit",
        )
        if not lesson_title_col and lesson_id_col:
            lesson_title_col = lesson_id_col
        if not lesson_id_col and lesson_title_col:
            lesson_id_col = lesson_title_col

        if lesson_id_col:
            df["_lesson_raw"] = df[lesson_id_col].fillna("").astype(str)
        else:
            df["_lesson_raw"] = ""
        if lesson_title_col:
            df["_lesson_title"] = df[lesson_title_col].fillna("").astype(str)
        else:
            df["_lesson_title"] = ""

        df["_lesson_raw"] = df["_lesson_raw"].apply(lambda v: str(v).strip() or "__default__")
        df["_lesson_title"] = df["_lesson_title"].apply(lambda v: str(v).strip())

        self.df = df.fillna("")

        themes_in_order = list(dict.fromkeys(self.df["theme_id"].astype(str)))
        self._idx_to_theme: dict[str, str] = {str(i): t for i, t in enumerate(themes_in_order)}
        self._theme_to_idx: dict[str, str] = {t: str(i) for i, t in enumerate(themes_in_order)}
        self._theme_to_idx_lower: dict[str, str] = {str(t).lower(): idx for idx, t in self._idx_to_theme.items()}
        self._theme_order: list[str] = list(self._idx_to_theme.keys())

        self._theme_counts_raw: dict[str, int] = (
            self.df.groupby("theme_id").size().astype(int).to_dict()
            if "theme_id" in self.df.columns and not self.df.empty
            else {}
        )

        self._theme_idx_to_slug: dict[str, str] = {}
        self._theme_slug_to_idx: dict[str, str] = {}
        self._theme_value_to_slug: dict[str, str] = {}
        used_theme_slugs: set[str] = set()
        for idx, theme in self._idx_to_theme.items():
            base_slug = self._slugify(theme, f"theme-{idx}")
            slug = base_slug
            counter = 2
            while slug in used_theme_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            used_theme_slugs.add(slug)
            self._theme_idx_to_slug[idx] = slug
            self._theme_slug_to_idx[slug] = idx
            self._theme_value_to_slug[str(theme)] = slug
            self._theme_value_to_slug[str(theme).lower()] = slug

        self._lesson_idx_to_info: dict[str, dict[str, dict[str, str]]] = {}
        self._lesson_idx_order: dict[str, list[str]] = {}
        self._lesson_slug_to_idx: dict[str, dict[str, str]] = {}
        self._lesson_idx_to_slug: dict[str, dict[str, str]] = {}
        self._lesson_raw_to_idx: dict[str, dict[str, str]] = {}
        self._lesson_counts_by_idx: dict[str, dict[str, int]] = {}

        for idx, theme in self._idx_to_theme.items():
            theme_rows = self.df[self.df["theme_id"].astype(str) == str(theme)]
            raw_values = [str(v) for v in theme_rows["_lesson_raw"].tolist()]
            if not raw_values:
                raw_values = ["__default__"]
            lessons_raw_order = list(dict.fromkeys(raw_values))
            title_values = [str(v) for v in theme_rows["_lesson_title"].tolist()]
            raw_to_title: dict[str, str] = {}
            for raw_val, title_val in zip(raw_values, title_values):
                title_val = title_val.strip()
                if title_val and raw_val not in raw_to_title:
                    raw_to_title[raw_val] = title_val

            lesson_info_map: dict[str, dict[str, str]] = {}
            lesson_order: list[str] = []
            slug_map: dict[str, str] = {}
            idx_to_slug: dict[str, str] = {}
            raw_to_idx: dict[str, str] = {}
            counts_map: dict[str, int] = {}
            raw_counter = Counter(raw_values)
            used_lesson_slugs: set[str] = set()

            for order_idx, raw in enumerate(lessons_raw_order):
                lesson_idx = str(order_idx)
                title = raw_to_title.get(raw)
                if not title:
                    if raw == "__default__" and len(lessons_raw_order) == 1:
                        title = str(theme)
                    else:
                        title = f"Lesson {order_idx + 1}"
                base_slug_source = raw if raw != "__default__" else title
                base_slug = self._slugify(base_slug_source, f"lesson-{lesson_idx}")
                slug = base_slug
                counter = 2
                while slug in used_lesson_slugs:
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                used_lesson_slugs.add(slug)

                lesson_info_map[lesson_idx] = {"raw": raw, "title": title, "slug": slug}
                lesson_order.append(lesson_idx)
                slug_map[slug] = lesson_idx
                idx_to_slug[lesson_idx] = slug
                raw_to_idx[raw] = lesson_idx
                counts_map[lesson_idx] = int(raw_counter.get(raw, 0))

            self._lesson_idx_to_info[idx] = lesson_info_map
            self._lesson_idx_order[idx] = lesson_order
            self._lesson_slug_to_idx[idx] = slug_map
            self._lesson_idx_to_slug[idx] = idx_to_slug
            self._lesson_raw_to_idx[idx] = raw_to_idx
            self._lesson_counts_by_idx[idx] = counts_map

        def to_theme_slug(value: str) -> str:
            value_str = str(value)
            key = self._theme_to_idx.get(value_str)
            if key and key in self._theme_idx_to_slug:
                return self._theme_idx_to_slug[key]
            key = self._theme_to_idx_lower.get(value_str.lower())
            if key and key in self._theme_idx_to_slug:
                return self._theme_idx_to_slug[key]
            return self._slugify(value_str, "theme")

        self.df["_theme_slug"] = self.df["theme_id"].astype(str).apply(to_theme_slug)

        def to_lesson_slug(row: pd.Series) -> str:
            theme_value = str(row.get("theme_id"))
            theme_key = self._theme_to_idx.get(theme_value)
            if not theme_key:
                theme_key = self._theme_to_idx_lower.get(theme_value.lower())
            if not theme_key:
                return ""
            raw = str(row.get("_lesson_raw", "__default__"))
            lesson_idx = self._lesson_raw_to_idx.get(theme_key, {}).get(raw)
            if not lesson_idx:
                return ""
            return self._lesson_idx_to_slug.get(theme_key, {}).get(lesson_idx, "")

        self.df["_lesson_slug"] = self.df.apply(to_lesson_slug, axis=1)

    # --- SEARCH HELPERS ---

    @staticmethod
    def _normalize_text(s: str) -> str:
        """
        Простая нормализация под поиск: нижний регистр, ё->е, убираем лишние символы,
        схлопываем пробелы.
        """
        s = (s or "").lower()
        s = s.replace("ё", "е")
        # разрешаем буквы/цифры/пробелы, остальное -> пробел
        s = re.sub(r"[^0-9a-zа-я\s]", " ", s, flags=re.IGNORECASE)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @staticmethod
    def _extract_query_terms(q: str) -> tuple[list[str], list[str]]:
        """
        Возвращает (tokens, phrases). Фразы — в двойных кавычках "..." или «...».
        Остальное — токены по пробелам.
        """
        if not q:
            return [], []
        # фразы в кавычках
        phrase_matches = re.findall(r'"([^"]+)"|«([^»]+)»', q)
        phrases = [m[0] or m[1] for m in phrase_matches]
        # убираем фразы из строки, чтобы не удвоить токены
        q_wo_phrases = re.sub(r'"[^"]+"|«[^»]+»', " ", q)
        tokens = [t for t in re.split(r"\s+", q_wo_phrases) if t]
        # нормализуем
        phrases = [PandasTaskRepo._normalize_text(p) for p in phrases if p.strip()]
        tokens = [PandasTaskRepo._normalize_text(t) for t in tokens if t.strip()]
        return tokens, phrases

    @staticmethod
    def _levenshtein_within(a: str, b: str, k: int = 1) -> bool:
        """
        Проверка расстояния Левенштейна <= k (по умолчанию 1) с ранним выходом.
        Оптимизировано узкой диагональной полосой (Ukkonen).
        """
        # быстрый отсев по длинам
        la, lb = len(a), len(b)
        if abs(la - lb) > k:
            return False
        # гарантируем a короче
        if la > lb:
            a, b = b, a
            la, lb = lb, la

        prev = list(range(la + 1))
        for j in range(1, lb + 1):
            bj = b[j - 1]
            start = max(1, j - k)
            end = min(la, j + k)
            cur = [0] * (la + 1)
            cur[0] = j
            # вне полосы — заполняем значениями > k, чтобы отсеять
            for i in range(1, start):
                cur[i] = k + 1
            for i in range(start, end + 1):
                cost = 0 if a[i - 1] == bj else 1
                cur[i] = min(
                    prev[i] + 1,       # удаление
                    cur[i - 1] + 1,    # вставка
                    prev[i - 1] + cost # замена/совпадение
                )
            for i in range(end + 1, la + 1):
                cur[i] = k + 1
            if min(cur) > k:
                return False
            prev = cur
        return prev[la] <= k

    def _score_text_for_query(self, text_norm: str, tokens: list[str], phrases: list[str]) -> int:
        """
        Вычисляет простой скоринг совпадений:
        +5 за каждую найденную фразу,
        +2 за точное вхождение токена,
        +1 за "почти-совпадение" (Левенштейн<=1 или подстрока для токенов >=4).
        """
        if not text_norm:
            return 0
        score = 0
        words = set(text_norm.split())

        # фразы с большим весом
        for ph in phrases:
            if ph and ph in text_norm:
                score += 5 * max(1, ph.count(" ") + 1)

        for t in tokens:
            if not t:
                continue
            if t in words or t in text_norm:
                score += 2
                continue
            # “мягкий” матч: опечатки и частичные совпадения
            near = False
            if len(t) >= 4:
                # подстрочное (для длинных токенов)
                for w in words:
                    if t in w or w in t:
                        near = True
                        break
            if not near:
                # Левенштейн<=1 на любое слово
                for w in words:
                    if self._levenshtein_within(t, w, k=1):
                        near = True
                        break
            if near:
                score += 1

        return score
    
    # --- OTHER HELPERS ---

    def _resolve_theme_key(self, theme_id: str | None) -> Optional[str]:
        if theme_id is None:
            return None
        candidate = str(theme_id).strip()
        if not candidate:
            return None
        if candidate in self._theme_slug_to_idx:
            return self._theme_slug_to_idx[candidate]
        if candidate in self._idx_to_theme:
            return candidate
        if candidate in self._theme_to_idx:
            return self._theme_to_idx[candidate]
        lower = candidate.lower()
        if lower in self._theme_to_idx_lower:
            return self._theme_to_idx_lower[lower]
        for idx, theme in self._idx_to_theme.items():
            if str(theme).lower() == lower:
                return idx
        return None

    def _resolve_lesson_key(self, theme_key: str, lesson_id: str | None) -> Optional[str]:
        if lesson_id is None:
            return None
        candidate = str(lesson_id).strip()
        if not candidate:
            return None
        slug_map = self._lesson_slug_to_idx.get(theme_key, {})
        if candidate in slug_map:
            return slug_map[candidate]
        info_map = self._lesson_idx_to_info.get(theme_key, {})
        if candidate in info_map:
            return candidate
        raw_map = self._lesson_raw_to_idx.get(theme_key, {})
        if candidate in raw_map:
            return raw_map[candidate]
        lower = candidate.lower()
        for idx, info in info_map.items():
            if info["title"].lower() == lower:
                return idx
        return None

    def _build_theme_payload(self, theme_key: str) -> Optional[dict]:
        slug = self._theme_idx_to_slug.get(theme_key)
        if not slug:
            return None
        title = str(self._idx_to_theme.get(theme_key, slug))
        lesson_info_map = self._lesson_idx_to_info.get(theme_key, {})
        lesson_order = self._lesson_idx_order.get(theme_key, list(lesson_info_map.keys()))
        lessons = []
        for lesson_idx in lesson_order:
            info = lesson_info_map.get(lesson_idx)
            if not info:
                continue
            lessons.append(
                {
                    "id": info["slug"],
                    "title": info["title"],
                    "description": "",
                    "tasks_count": self._lesson_counts_by_idx.get(theme_key, {}).get(lesson_idx, 0),
                    "theme_id": slug,
                }
            )
        total_count = sum(self._lesson_counts_by_idx.get(theme_key, {}).values())
        return {
            "id": slug,
            "title": title,
            "description": "",
            "tasks_count": total_count,
            "lessons": lessons,
        }

    def _row_to_task(self, row: pd.Series) -> Task:
        tags_raw = row.get("tags", "")
        tags = [t.strip() for t in str(tags_raw).split(",") if t.strip()] if tags_raw else []
        theme_value = str(row.get("theme_id", "math"))
        theme_key = self._theme_to_idx.get(theme_value)
        if not theme_key:
            theme_key = self._theme_to_idx_lower.get(theme_value.lower())
        theme_slug = self._theme_idx_to_slug.get(theme_key, self._slugify(theme_value, "theme"))
        lesson_slug = None
        lesson_title = None
        if theme_key:
            raw = str(row.get("_lesson_raw", "__default__"))
            lesson_idx = self._lesson_raw_to_idx.get(theme_key, {}).get(raw)
            if lesson_idx:
                lesson_slug = self._lesson_idx_to_slug.get(theme_key, {}).get(lesson_idx)
                lesson_info = self._lesson_idx_to_info.get(theme_key, {}).get(lesson_idx, {})
                lesson_title = lesson_info.get("title")
        return Task(
            id=str(row["id"]),
            theme_id=theme_slug,
            theme_title=theme_value,
            name=str(row["name"]),
            difficulty=str(row.get("difficulty", "easy")),
            statement_md=str(row["statement_md"]),
            reference_solution_md=str(row.get("reference_solution_md") or ""),
            source=str(row.get("source") or ""),
            tags=tags,
            lesson_id=lesson_slug,
            lesson_title=lesson_title,
        )

    async def get(self, task_id: str) -> Task | None:
        rows = self.df[self.df["id"].astype(str) == str(task_id)]
        if rows.empty:
            return None
        return self._row_to_task(rows.iloc[0])

    async def list(
        self,
        theme_id: str | None = None,
        lesson_id: str | None = None,
        difficulty: str | None = None,
        tags: str | None = None,
        q: str | None = None,
        sort_by: str | None = None,
        seed: int | None = None,
        limit: int = 50,
        offset: int = 0,
        exclude_solved_by_user_id: str | None = None,
        attempts_repo=None,

        # НОВОЕ:
        theme_ids: list[str] | None = None,
        difficulty_in: list[str] | None = None,
    ):
        df = self.df

        # ---- ТЕМЫ: OR-фильтр по нескольким значениям ----
        if theme_ids:
            allowed_slugs: set[str] = set()
            allowed_raws: set[str] = set()
            for tid in theme_ids:
                key = self._resolve_theme_key(tid)
                if key:
                    slug = self._theme_idx_to_slug.get(key)
                    if slug:
                        allowed_slugs.add(slug)
                else:
                    # если не распознали как slug/индекс — попробуем сравнить с исходной колонкой theme_id
                    allowed_raws.add(str(tid))
            mask = None
            if allowed_slugs:
                mask = df["_theme_slug"].isin(list(allowed_slugs))
            if allowed_raws:
                raw_mask = df["theme_id"].astype(str).isin(list(allowed_raws))
                mask = raw_mask if mask is None else (mask | raw_mask)
            if mask is not None:
                df = df[mask]
        else:
            # старый одиночный фильтр (как было)
            theme_key = self._resolve_theme_key(theme_id)
            if theme_key:
                theme_slug = self._theme_idx_to_slug.get(theme_key)
                df = df[df["_theme_slug"] == theme_slug]
            elif theme_id:
                df = df[df["theme_id"].astype(str) == str(theme_id)]

        # ---- УРОВНИ СЛОЖНОСТИ: OR-фильтр по нескольким ----
        if difficulty_in:
            norm = set()
            for d in difficulty_in:
                s = str(d).strip().lower()
                if s in ("легкий", "лёгкий", "easy", "простой"):
                    norm.add("easy")
                elif s in ("средний", "medium", "нормальный"):
                    norm.add("medium")
                elif s in ("сложный", "hard", "тяжелый", "тяжёлый"):
                    norm.add("hard")
            if norm:
                df = df[df["difficulty"].astype(str).isin(list(norm))]
        elif difficulty:
            df = df[df["difficulty"].astype(str) == str(difficulty)]

        # ---- остальное как было ----
        if lesson_id:
            lesson_filtered = False
            # если выше был выбран конкретный theme_key — логика как раньше;
            # при множественных темах сюда обычно не попадём с lesson_id.
            theme_key = self._resolve_theme_key(theme_id) if (theme_id and not theme_ids) else None
            if theme_key:
                lesson_key = self._resolve_lesson_key(theme_key, lesson_id)
                lesson_filtered = True
                if lesson_key is None:
                    df = df.iloc[0:0]
                else:
                    raw = self._lesson_idx_to_info.get(theme_key, {}).get(lesson_key, {}).get("raw")
                    if raw is None:
                        df = df.iloc[0:0]
                    else:
                        df = df[df["_lesson_raw"] == raw]
            if not lesson_filtered:
                df = df[df["_lesson_slug"] == str(lesson_id)]

        if tags:
            tagset = {t.strip().lower() for t in tags.split(",") if t.strip()}
            if tagset:
                df = df[
                    df["tags"].str.lower().apply(
                        lambda x: tagset.issubset({t.strip() for t in str(x).split(",") if t.strip()})
                    )
                ]

        if q:
            tokens, phrases = self._extract_query_terms(q)

            # Собираем поле для поиска: name + statement_md (+ можно добавить tags/source)
            search_series = (
                df.get("name", "").astype(str) + " " +
                df.get("statement_md", "").astype(str)
                # + " " + df.get("tags", "").astype(str)
                # + " " + df.get("source", "").astype(str)
            )

            # Нормализуем один раз
            search_norm = search_series.map(self._normalize_text)

            # Считаем скоринг
            scores = search_norm.map(lambda txt: self._score_text_for_query(txt, tokens, phrases))

            # Оставляем только релевантные и сортируем по убыванию очков
            df = df.loc[scores > 0].assign(_score=scores[scores > 0]).sort_values("_score", ascending=False)

        if exclude_solved_by_user_id and attempts_repo:
            solved_task_ids = set()
            for a in await attempts_repo.list_by_user(exclude_solved_by_user_id):
                if is_attempt_solved(a.get("score"), a.get("feedback")):
                    solved_task_ids.add(a["task_id"])
            df = df[~df["id"].astype(str).isin(solved_task_ids)]

        if sort_by == "random":
            df = df.sample(frac=1.0, random_state=seed if seed is not None else None)
        elif sort_by == "difficulty":
            order = {"easy": 0, "medium": 1, "hard": 2}
            df = df.sort_values(by="difficulty", key=lambda s: s.map(lambda x: order.get(str(x), 1)))

        out = [self._row_to_task(r) for _, r in df.iloc[offset : offset + limit].iterrows()]
        return out

    async def list_themes(self):
        if "theme_id" not in self.df.columns or self.df.empty:
            return [
                {
                    "id": "math",
                    "title": "математика",
                    "description": "",
                    "tasks_count": 0,
                    "lessons": [],
                }
            ]

        items = []
        for theme_key in self._theme_order:
            payload = self._build_theme_payload(theme_key)
            if payload:
                items.append(payload)
        return items

    async def get_theme(self, theme_id: str):
        theme_key = self._resolve_theme_key(theme_id)
        if not theme_key:
            return None
        return self._build_theme_payload(theme_key)

    async def get_lesson(self, theme_id: str, lesson_id: str):
        theme_key = self._resolve_theme_key(theme_id)
        if not theme_key:
            return None
        lesson_key = self._resolve_lesson_key(theme_key, lesson_id)
        if not lesson_key:
            return None
        info = self._lesson_idx_to_info.get(theme_key, {}).get(lesson_key)
        if not info:
            return None
        theme_slug = self._theme_idx_to_slug.get(theme_key)
        return {
            "id": info["slug"],
            "title": info["title"],
            "description": "",
            "tasks_count": self._lesson_counts_by_idx.get(theme_key, {}).get(lesson_key, 0),
            "theme_id": theme_slug,
        }

    async def daily_task(self):
        today = datetime.date.today()
        if self.df.empty:
            empty_task = Task(
                id="0",
                theme_id="math",
                theme_title="math",
                name="Задача",
                difficulty="easy",
                statement_md="(пусто)",
                reference_solution_md="",
                source="",
                tags=[],
                lesson_id=None,
                lesson_title=None,
            )
            return {"date": str(today), "task": empty_task}
        idx = int(today.strftime("%Y%m%d")) % len(self.df)
        print(idx)
        r = self.df.iloc[idx]
        t = self._row_to_task(r)
        return {"date": str(today), "task": t}
