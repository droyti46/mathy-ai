# app/api/routers/submit.py (фрагменты)
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.api.schemas.attempt import AttemptIn, AttemptOut, Feedback, Span
from app.api.schemas.auth import StatsOut
from app.core.deps import get_uow, get_llm, get_ocr, get_user_opt
from datetime import datetime, timezone
from app.infrastructure.ocr.vision_openrouter import VisionOCROpenRouter
from app.application.markers import postprocess_marked_text
from app.core.user_stats import maybe_update_user_stats, resolve_user_id
from app.core.attempts import is_attempt_solved

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

router = APIRouter(prefix="/submit", tags=["submit"])

def _build_feedback(raw_result: dict) -> Feedback:
    """
    Принимает сырые данные от градерa и формирует Feedback:
    - feedback.spans => [[start,end], ...] (используются только внутри бэкенда)
    - feedback.spans_detail => List[Span]
    """

    raw_spans = raw_result.get("spans", []) or []
    spans_detail: list[Span] = []
    spans_pairs: list[list[int]] = []

    if raw_spans and isinstance(raw_spans[0], list):
        # Уже в формате [[a,b],...]
        spans_pairs = [[int(a), int(b)] for a, b in raw_spans if isinstance(a, (int, float)) and isinstance(b, (int, float))]
        # Деталей может не быть — оставим пустыми
    else:
        # Ожидаем объекты {start,end,message?,severity?}
        for s in raw_spans:
            if not isinstance(s, dict):
                continue
            start = int(s.get("start", 0))
            end = int(s.get("end", 0))
            msg = str(s.get("message", ""))
            sev = str(s.get("severity", "info"))
            spans_detail.append(Span(start=start, end=end, message=msg, severity=sev))
            spans_pairs.append([start, end])

    return Feedback(spans=spans_pairs, spans_detail=spans_detail)

@router.post("", response_model=AttemptOut)
async def create_attempt(
    payload: AttemptIn,
    uow = Depends(get_uow),
    llm = Depends(get_llm),
    user = Depends(get_user_opt),
):
    # 1) проверка задачи
    task = await uow.tasks.get(payload.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 2) LLM теперь возвращает размеченный текст с <w message="...">...</w>
    marked = await llm.check_solution(task.statement_md, payload.text)
    stitched_solution, marker_spans, marker_msgs = postprocess_marked_text(payload.text, marked)

    spans_detail = [
        Span(start=s, end=e, message=(marker_msgs[i] if i < len(marker_msgs) else ""), severity="error")
        for i, (s, e) in enumerate(marker_spans)
    ]
    feedback = Feedback(spans=marker_spans, spans_detail=spans_detail)

    now = _now_iso()
    user_id = await resolve_user_id(uow, user, payload.login)

    attempt_id = await uow.attempts.save({
        "task_id": payload.task_id,
        "solution_text": payload.text,
        "feedback": feedback.model_dump(),
        "created_at": now,
        "user_id": user_id,
    })

    is_solved = is_attempt_solved(feedback)

    stats_result = await maybe_update_user_stats(
        uow, user_id, payload.task_id, task.difficulty, is_solved
    )

    stats_out: StatsOut | None = None
    coins_rewarded = 0
    if stats_result:
        stats_out, is_solved, coins_rewarded = stats_result

    return AttemptOut(
        id=str(attempt_id),
        task_id=payload.task_id,
        solution_text=payload.text,
        feedback=feedback,
        created_at=now,
        is_solved=is_solved,
        coins_rewarded=coins_rewarded,
        stats=stats_out,
    )

@router.post("/extract_text_from_file", response_model=str)
async def extract_text(
    file: UploadFile = File(...),
    ocr: VisionOCROpenRouter = Depends(get_ocr),
):
    # OCR
    text = await ocr.extract_text(file)
    return text