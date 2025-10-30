from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from sqlalchemy import select, insert, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import models as m


def _to_iso_utc(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


def _attempt_to_dict(a: m.Attempt) -> Dict[str, Any]:
    return {
        "id": a.id,
        "task_id": a.task_id,
        "user_id": a.user_id,
        "text": a.text or "",
        "file": a.file,
        "feedback": a.feedback,
        "created_at": _to_iso_utc(a.created_at),
        "mode": a.mode,
        "score": a.score,
        "time_spent_sec": a.time_spent_sec,
    }


def _user_to_dict(u: m.User) -> Dict[str, Any]:
    return {
        "id": u.id,
        "login": u.login,
        "password_hash": u.password_hash,
        "created_at": _to_iso_utc(u.created_at),
    }


class SqlAttemptRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    # Оставим для обратной совместимости (как у тебя было). Не используем в новых местах.
    async def add(self, attempt: dict) -> None:
        await self.session.execute(insert(m.Attempt).values(**attempt))
        await self.session.commit()

    async def get(self, attempt_id: str) -> Optional[dict]:
        res = await self.session.execute(
            select(m.Attempt).where(m.Attempt.id == attempt_id)
        )
        row = res.scalar_one_or_none()
        return _attempt_to_dict(row) if row else None

    async def list(
        self,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        stmt = select(m.Attempt)
        if task_id:
            stmt = stmt.where(m.Attempt.task_id == task_id)
        if user_id:
            stmt = stmt.where(m.Attempt.user_id == user_id)
        stmt = stmt.order_by(desc(m.Attempt.created_at)).offset(offset).limit(limit)
        res = await self.session.execute(stmt)
        rows = res.scalars().all()
        return [_attempt_to_dict(r) for r in rows]

    async def list_by_user(self, user_id: str) -> List[dict]:
        res = await self.session.execute(
            select(m.Attempt).where(m.Attempt.user_id == user_id)
        )
        rows = res.scalars().all()
        return [_attempt_to_dict(r) for r in rows]

    async def save(self, data: Dict[str, Any]) -> str:
        """
        Ожидает словарь:
          task_id: str
          mode: str
          solution_text | text: str
          feedback: dict | JSON-serializable
          score: float | None
          time_spent_sec: int | None
          user_id: str | None
          created_at: ISO str | datetime | None
        Возвращает id (str).
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except Exception:
                created_at = datetime.now(timezone.utc)
        elif not isinstance(created_at, datetime):
            created_at = datetime.now(timezone.utc)

        values = {
            "task_id": str(data["task_id"]),
            "user_id": data.get("user_id"),
            # в модели колонка называется text — кладём туда то, что приходит как solution_text/text
            "text": data.get("solution_text") or data.get("text") or "",
            "file": data.get("file"),
            "feedback": data.get("feedback"),   # JSON-колонка
            "mode": data.get("mode", "solve"),
            "score": data.get("score"),
            "time_spent_sec": data.get("time_spent_sec"),
            "created_at": created_at,
        }

        stmt = insert(m.Attempt).values(**values).returning(m.Attempt.id)
        res = await self.session.execute(stmt)
        new_id = res.scalar_one()
        await self.session.commit()
        return str(new_id)


class SqlUserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user: dict):
        await self.session.execute(insert(m.User).values(**user))
        await self.session.commit()

    async def get(self, user_id: str) -> Optional[dict]:
        res = await self.session.execute(select(m.User).where(m.User.id == user_id))
        row = res.scalar_one_or_none()
        return _user_to_dict(row) if row else None

    async def get_by_login(self, login: str) -> Optional[dict]:
        res = await self.session.execute(select(m.User).where(m.User.login == login))
        row = res.scalar_one_or_none()
        return _user_to_dict(row) if row else None
