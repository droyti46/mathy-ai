from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_uow, get_llm, get_user_opt
from app.api.schemas.chat import ChatRequest, ChatOut, ChatMessage
from app.api.schemas.attempt import TeacherAttemptOut
from app.core.user_stats import maybe_update_user_stats, resolve_user_id

router = APIRouter(prefix="/tasks", tags=["teacher"])

@router.post("/{task_id}/teacher/init", response_model=ChatOut)
async def init_teacher_mode(task_id: str, uow = Depends(get_uow), llm = Depends(get_llm)):
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    text = await llm.init_teacher_mode(task)
    return ChatOut(messages=[ChatMessage(role="assistant", content=text)])

@router.post("/{task_id}/teacher", response_model=TeacherAttemptOut)
async def teacher_message(
    task_id: str,
    payload: ChatRequest,
    login: Optional[str] = None,
    llm = Depends(get_llm),
    uow = Depends(get_uow),
    user = Depends(get_user_opt),
):
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    text = await llm.teacher_message(task, [{"role": "user", "content": ""}] + [m.model_dump() for m in payload.messages])

    user_id = await resolve_user_id(uow, user, login)

    # Проверка на то, что задача решена
    is_solved = 'задача решена' in text.lower()

    # Получаем статистику пользователя
    stats_result = await maybe_update_user_stats(
        uow, user_id, task_id, task.difficulty, is_solved
    )
    stats_out, is_solved, coins_rewarded = stats_result

    # Возвращаем результат
    return TeacherAttemptOut(
        task_id=task_id,
        messages=[ChatMessage(role="assistant", content=text)],
        is_solved=is_solved,
        coins_rewarded=coins_rewarded,
        stats=stats_out
    )