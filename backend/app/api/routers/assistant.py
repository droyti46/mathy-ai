# api/assistant.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.core.deps import get_uow, get_llm
from app.api.schemas.chat import ChatRequest, ChatOut, ChatMessage

router = APIRouter(prefix="/tasks", tags=["assistant"])

@router.post("/{task_id}/assistant", response_model=ChatOut)
async def request_hint(task_id: str, payload: ChatRequest, uow=Depends(get_uow), llm=Depends(get_llm)):
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    text = await llm.hint(task.statement_md, [m.model_dump() for m in payload.messages])
    return ChatOut(messages=[ChatMessage(role="assistant", content=text)])

# НОВОЕ: стрим
@router.post("/{task_id}/assistant/stream")
async def request_hint_stream(task_id: str, payload: ChatRequest, uow=Depends(get_uow), llm=Depends(get_llm)):
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def gen():
        async for tok in llm.hint_stream(task.statement_md, [m.model_dump() for m in payload.messages]):
            yield tok

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # выключить буферизацию nginx, если есть
    }
    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8", headers=headers)
