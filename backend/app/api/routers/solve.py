from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_uow, get_llm
from app.api.schemas.chat import ChatOut, ChatMessage

router = APIRouter(prefix="/tasks", tags=["solver"])

@router.post("/{task_id}/solve", response_model=ChatOut)
async def solve_task(task_id: str, uow = Depends(get_uow), llm = Depends(get_llm)):
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    text = await llm.solve(task)
    return ChatOut(messages=[ChatMessage(role="assistant", content=text)])