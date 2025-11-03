from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_uow, get_user_opt
from app.core.user_stats import resolve_user_id
from app.core.attempts import is_attempt_solved
from app.api.schemas.attempt import AttemptOut, Feedback  # ваши уже существующие схемы

router = APIRouter(prefix="/tasks", tags=["tasks"])  # можно оставить в "tasks" ради REST: /tasks/{id}/attempts

@router.get("/{task_id}/attempts", response_model=List[AttemptOut])
async def list_my_attempts_for_task(
    task_id: str,
    login: Optional[str] = None,                       # как и в других ваших эндпоинтах
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow = Depends(get_uow),
    user = Depends(get_user_opt),
):
    # 1) проверяем, что задача существует — чтобы не светить наличие попыток «в никуда»
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # 2) определяем текущего пользователя (по токену или login)
    user_id = await resolve_user_id(uow, user, login)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    # 3) получаем попытки по (task_id, user_id) с пагинацией
    rows = await uow.attempts.list(task_id=task_id, user_id=user_id, limit=limit, offset=offset)

    # 4) маппим в AttemptOut (repo возвращает "text" — кладём в "solution_text")
    out: List[AttemptOut] = []
    for r in rows:
        fb = r.get("feedback") or {}
        solved = is_attempt_solved(fb)
        out.append(AttemptOut(
            id=str(r["id"]),
            task_id=str(r["task_id"]),
            solution_text=r.get("text") or "",
            feedback=fb,                       # Pydantic вложенную схему соберёт из dict
            created_at=r.get("created_at"),
            is_solved=solved,
            # coins_rewarded / stats тут не формируем — это список попыток
        ))

    return out
