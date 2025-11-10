# app/api/routes/tasks.py (или где у тебя этот роут)
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from app.core.deps import get_uow, get_user_opt
from app.api.schemas.task import TaskOut, DailyTaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])

def _split_csv(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]

@router.get("/daily", response_model=DailyTaskOut)
async def daily_task(uow = Depends(get_uow)):
    t = await uow.tasks.daily_task()
    return DailyTaskOut(date=t["date"], task=TaskOut(**t["task"].__dict__))

@router.get("", response_model=list[TaskOut])
async def list_tasks(
    theme_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    difficulty: Optional[str] = Query(default=None),
    tags: Optional[str] = None,
    q: Optional[str] = None,
    exclude_solved: bool = False,
    sort_by: Optional[str] = None,
    seed: Optional[int] = None,
    limit: int = 50, offset: int = 0,
    uow = Depends(get_uow),
    user = Depends(get_user_opt),
):
    theme_ids = _split_csv(theme_id)
    difficulty_in = _split_csv(difficulty)

    tasks = await uow.tasks.list(
        # новые аргументы (списки, если пусто — None)
        theme_ids = theme_ids or None,
        difficulty_in = difficulty_in or None,

        # старые — оставляем для обратной совместимости (но они будут проигнорированы,
        # если переданы списки выше)
        theme_id = None if theme_ids else theme_id,
        lesson_id = lesson_id,
        difficulty = None if difficulty_in else difficulty,
        tags = tags,
        q = q,
        sort_by = sort_by,
        seed = seed,
        limit = limit,
        offset = offset,
        exclude_solved_by_user_id=(user["user_id"] if user and exclude_solved else None),
        attempts_repo=uow.attempts,
    )
    return [TaskOut(**t.__dict__) for t in tasks]


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, uow = Depends(get_uow)):
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut(**task.__dict__)