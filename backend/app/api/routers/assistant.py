from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_uow, get_llm
from app.api.schemas.chat import HintRequest, HintOut, ChatMessage

router = APIRouter(prefix="/tasks", tags=["assistant"])

@router.post("/{task_id}/assistant", response_model=HintOut)
async def request_hint(
    task_id: str,
    payload: HintRequest,
    uow = Depends(get_uow),
    llm = Depends(get_llm),
):
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    text = await llm.hint(task.statement_md, [m.model_dump() for m in payload.messages])
    return HintOut(messages=[ChatMessage(role="assistant", content=text)], model="openrouter")
