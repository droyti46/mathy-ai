from __future__ import annotations
import pandas as pd, random, datetime
from app.domain.tasks.entities import Task
from app.core.attempts import is_attempt_solved

class PandasTaskRepo:
    def __init__(self, path: str):
        self.path = path
        df = pd.read_csv(path)

        columns_lower = {str(c).strip().lower(): c for c in df.columns}

        def pick(*names):
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
        self.df = df.fillna("")

    async def get(self, task_id: str) -> Task | None:
        rows = self.df[self.df["id"].astype(str) == str(task_id)]
        if rows.empty:
            return None
        r = rows.iloc[0]
        tags = r.get("tags", "")
        tags = [t.strip() for t in str(tags).split(",")] if tags else []
        return Task(id=str(r["id"]), theme_id=str(r.get("theme_id","math")), name=str(r['name']),
                    difficulty=str(r.get("difficulty","easy")), statement_md=str(r["statement_md"]),
                    reference_solution_md=str(r.get("reference_solution_md") or ""), source=str(r.get("source") or ""), tags=tags)

    async def list(self, theme_id: str | None = None, difficulty: str | None = None, tags: str | None = None,
                   q: str | None = None, sort_by: str | None = None, seed: int | None = None,
                   limit: int = 50, offset: int = 0,
                   exclude_solved_by_user_id: str | None = None, attempts_repo=None):
        df = self.df
        if theme_id:
            df = df[df["theme_id"].astype(str) == str(theme_id)]
        if difficulty:
            df = df[df["difficulty"].astype(str) == str(difficulty)]
        if tags:
            tagset = {t.strip().lower() for t in tags.split(",") if t.strip()}
            if tagset:
                df = df[df["tags"].str.lower().apply(lambda x: tagset.issubset(set([t.strip() for t in str(x).split(",") if t.strip()])))]
        if q:
            ql = q.lower()
            df = df[df["statement_md"].str.lower().str.contains(ql, na=False)]

        if exclude_solved_by_user_id and attempts_repo:
            solved_task_ids = set()
            for a in await attempts_repo.list_by_user(exclude_solved_by_user_id):
                if is_attempt_solved(a.get("score"), a.get("feedback")):
                    solved_task_ids.add(a["task_id"])
            df = df[~df["id"].astype(str).isin(solved_task_ids)]

        if sort_by == "random":
            df = df.sample(frac=1.0, random_state=seed if seed is not None else None)
        elif sort_by == "difficulty":
            order = {"easy":0,"medium":1,"hard":2}
            df = df.sort_values(by="difficulty", key=lambda s: s.map(lambda x: order.get(str(x), 1)))

        out = []
        for _, r in df.iloc[offset: offset+limit].iterrows():
            tags = r.get("tags", "")
            tags = [t.strip() for t in str(tags).split(",")] if tags else []
            out.append(Task(id=str(r["id"]), theme_id=str(r.get("theme_id","math")), name=str(r['name']),
                            difficulty=str(r.get("difficulty","easy")), statement_md=str(r["statement_md"]),
                            reference_solution_md=str(r.get("reference_solution_md") or ""), source=str(r.get("source") or ""), tags=tags))
        return out

    async def list_themes(self):
        if "theme_id" not in self.df.columns or self.df.empty:
            return [{"id":"math","title":"Математика", "count": 0, "description": ""}]
        g = self.df.groupby("theme_id").size().reset_index(name="count")
        return [{"id": str(r["theme_id"]), "title": str(r["theme_id"]).title(), "count": int(r["count"]), "description": ""} for _, r in g.iterrows()]

    async def get_theme(self, theme_id: str):
        lst = await self.list_themes()
        for t in lst:
            if t["id"] == theme_id:
                return t
        return {"id": theme_id, "title": theme_id.title(), "count": 0, "description": ""}

    async def daily_task(self):
        today = datetime.date.today()
        if self.df.empty:
            return {"date": str(today), "task": Task(id="0", theme_id="math", difficulty="easy", statement_md="(пусто)")}
        idx = int(today.strftime("%Y%m%d")) % len(self.df)
        r = self.df.iloc[idx]
        t = Task(id=str(r["id"]), theme_id=str(r.get("theme_id","math")), difficulty=str(r.get("difficulty","easy")),
                 statement_md=str(r["statement_md"]), reference_solution_md=str(r.get("reference_solution_md") or ""),
                 source=str(r.get("source") or ""), tags=[t.strip() for t in str(r.get("tags","")).split(",") if t.strip()])
        return {"date": str(today), "task": t}
