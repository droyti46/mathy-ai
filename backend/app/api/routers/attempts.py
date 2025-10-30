# app/api/routers/attempts.py (фрагменты)
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.api.schemas.attempt import AttemptIn, AttemptOut, Feedback, Span
from app.core.deps import get_uow, get_llm, get_ocr
from datetime import datetime, timezone
from app.infrastructure.ocr.vision_openrouter import VisionOCROpenRouter
from app.application.markers import postprocess_marked_text

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

router = APIRouter(prefix="/attempts", tags=["attempts"])

def _build_feedback(raw_result: dict) -> Feedback:
    """
    Принимает сырые данные от градерa и формирует Feedback:
    - feedback.spans => [[start,end], ...]
    - feedback.spans_detail => List[Span]
    """
    summary = raw_result.get("summary", "")

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

    return Feedback(summary=summary, spans=spans_pairs, spans_detail=spans_detail)

@router.post("", response_model=AttemptOut)
async def create_attempt(
    payload: AttemptIn,
    uow = Depends(get_uow),
    llm = Depends(get_llm),
):
    # 1) проверка задачи
    task = await uow.tasks.get(payload.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 2) оценка LLM (градер)
    result = await llm.grade(task.statement_md, payload.text, reference=task.reference_solution_md)

    fb = _build_feedback(result)
    score = result.get("score") if isinstance(result, dict) else None

    marked = await llm.mark_errors(task.statement_md, payload.text)
    stitched_solution, marker_spans = postprocess_marked_text(payload.text, marked)

    if not fb.spans and marker_spans:
        fb.spans = marker_spans
    if not fb.spans_detail and marker_spans:
        fb.spans_detail = [Span(start=s, end=e) for s, e in marker_spans]

    now = _now_iso()

    attempt_id = await uow.attempts.save({
        "task_id": payload.task_id,
        "mode": payload.mode,
        "solution_text": stitched_solution,   # ← сохраняем размеченный текст
        "feedback": fb.model_dump(),
        "score": score,
        "time_spent_sec": payload.time_spent_sec,
        "created_at": now,
    })

    return AttemptOut(
        id=str(attempt_id),
        task_id=payload.task_id,
        solution_text=stitched_solution,
        feedback=fb,
        score=score,
        created_at=now,
    )

@router.post("/file", response_model=AttemptOut)
async def create_attempt_file(
    task_id: str,
    file: UploadFile = File(...),
    uow = Depends(get_uow),
    ocr: VisionOCROpenRouter = Depends(get_ocr),
    llm = Depends(get_llm),
):
    # 1) проверка задачи
    task = await uow.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 2) OCR → text
    text = await ocr.extract_text(file)
    marked = await llm.mark_errors(task.statement_md, text)
    stitched_solution, marker_spans = postprocess_marked_text(text, marked)

    feedback = Feedback(summary="", spans=marker_spans, spans_detail=[Span(start=s, end=e) for s, e in marker_spans])

    now = _now_iso()

    attempt_id = await uow.attempts.save({
        "task_id": task_id,
        "mode": "solve",
        "solution_text": stitched_solution,
        "feedback": feedback.model_dump(),
        "score": None,
        "created_at": now,
    })

    return AttemptOut(
        id=str(attempt_id),
        task_id=task_id,
        solution_text=stitched_solution,
        feedback=feedback,
        score=None,
        created_at=now,
    )
