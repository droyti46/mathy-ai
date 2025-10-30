from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_uow, get_llm
from app.api.schemas.chat import HintRequest, HintOut, ChatMessage

router = APIRouter(prefix="/tasks", tags=["hints"])

GUARD_PHRASES = ["полное решение", "дай ответ", "скажи ответ", "реши полностью", "final answer"]

@router.post("/{task_id}/hint", response_model=HintOut)
async def request_hint(task_id: str, payload: HintRequest, uow = Depends(get_uow), llm = Depends(get_llm)):
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if any(p in (payload.messages[-1].content.lower() if payload.messages else "") for p in GUARD_PHRASES):
        return HintOut(messages=[ChatMessage(role="assistant", content="Подумайте, какое определение/формулу здесь уместно применить. Начните с разбиения задачи на подшаги.")])
    text = await llm.hint(task.statement_md, [m.model_dump() for m in payload.messages])
    return HintOut(messages=[ChatMessage(role="assistant", content=text)], model="openrouter")
