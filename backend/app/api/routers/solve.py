from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.deps import get_uow, get_llm, get_user_opt
from app.core.user_stats import ensure_user_stats, resolve_user_id
from app.api.schemas.chat import ChatOut, ChatMessage

router = APIRouter(prefix="/tasks", tags=["solver"])
COST_SOLVE = 13

@router.post("/{task_id}/solve", response_model=ChatOut)
async def solve_task(
    task_id: str,
    login: Optional[str] = None,
    uow = Depends(get_uow),
    llm = Depends(get_llm),
    user = Depends(get_user_opt),
):
    user_id = await resolve_user_id(uow, user, login)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth required")

    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # --- атомарное списание монет ---
    async with uow:  # предполагаю, что ваш UoW поддерживает транзакции через async context
        db_user = await uow.users.get(user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        stats = ensure_user_stats(db_user.get("stats"))
        coins = int(stats.get("coins", 0))

        if coins < COST_SOLVE:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={"code": "INSUFFICIENT_FUNDS", "coins": coins, "required": COST_SOLVE},
            )

        # Обновляем локально
        stats["coins"] = coins - COST_SOLVE
        await uow.users.update_stats(user_id, stats)
        await uow.commit()  # фиксируем списание

    # --- решаем задачу (вне транзакции БД) ---
    try:
        text = await llm.solve(task)
    except Exception:
        # Опционально: вернуть монеты, если решение не удалось
        db_user = await uow.users.get(user_id)
        stats = ensure_user_stats(db_user.get("stats"))
        stats["coins"] = int(stats.get("coins", 0)) + COST_SOLVE
        await uow.users.update_stats(user_id, stats)
        # не коммитим молча: пусть пользователь увидит ошибку
        raise HTTPException(status_code=500, detail="Solver error")

    return ChatOut(messages=[ChatMessage(role="assistant", content=text)])
