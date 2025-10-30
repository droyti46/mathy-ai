from typing import Protocol, Iterable, Optional
from .entities import Task

class ITaskRepo(Protocol):
    async def get(self, task_id: str) -> Task | None: ...
    async def list(self, theme_id: Optional[str] = None,
                   difficulty: Optional[str] = None,
                   tags: Optional[str] = None,
                   q: Optional[str] = None,
                   sort_by: Optional[str] = None,
                   seed: Optional[int] = None,
                   limit: int = 50, offset: int = 0,
                   exclude_solved_by_user_id: str | None = None,
                   attempts_repo = None) -> Iterable[Task]: ...
    async def list_themes(self) -> list[dict]: ...
    async def get_theme(self, theme_id: str) -> dict: ...
    async def daily_task(self) -> dict: ...
