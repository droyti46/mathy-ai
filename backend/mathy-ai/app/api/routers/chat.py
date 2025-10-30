from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_uow, get_llm

router = APIRouter(prefix="/chat", tags=["chat"])

class HintIn(BaseModel):
    task_id: str
    text: str
    level: int = 1   # 1 — мягко, 2 — конкретнее, 3 — почти пошагово

class HintOut(BaseModel):
    hint: str

@router.post("/hint", response_model=HintOut)
async def chat_hint(payload: HintIn, uow = Depends(get_uow), llm = Depends(get_llm)):
    task = await uow.tasks.get(payload.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    hint_text = await llm.hint_from_text(task.statement_md, payload.text, level=payload.level)
    return HintOut(hint=hint_text)

@router.get("")
async def stub():
    return {"ok": True}
