from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_uow, get_llm
from app.core.security import teacher_mode_guard
from app.api.schemas.chat import SolutionOut, SolutionStep

router = APIRouter(prefix="/tasks", tags=["teacher"])

@router.post("/{task_id}/solve", response_model=SolutionOut)
async def solve_task(task_id: str, uow = Depends(get_uow), llm = Depends(get_llm), _: bool = Depends(teacher_mode_guard)):
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    solution = await llm.solve(task.statement_md)
    steps = []
    parts = [p for p in solution.split("\n## ") if p.strip()]
    if parts:
        steps.append(SolutionStep(title="Шаг 1", content_md=parts[0]))
        for i, p in enumerate(parts[1:], start=2):
            steps.append(SolutionStep(title=f"Шаг {i}", content_md=p))
    else:
        steps.append(SolutionStep(title="Решение", content_md=solution))
    return SolutionOut(steps=steps, final_answer_md=None)
