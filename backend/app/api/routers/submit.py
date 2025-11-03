# app/api/routers/attempts.py (фрагменты)
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.api.schemas.attempt import AttemptIn, AttemptOut, Feedback, Span
from app.api.schemas.auth import StatsOut
from app.core.deps import get_uow, get_llm, get_ocr, get_user_opt
from datetime import datetime, timezone
from app.infrastructure.ocr.vision_openrouter import VisionOCROpenRouter
from app.application.markers import postprocess_marked_text
from app.core.user_stats import coins_for_difficulty, ensure_user_stats
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

async def _resolve_user_id(uow, user: dict | None, login: str | None) -> str | None:
    if user and user.get("user_id"):
        return user.get("user_id")

    if login:
        db_user = await uow.users.get_by_login(login)
        if db_user:
            return db_user.get("id")

    return None

async def _maybe_update_user_stats(
    uow,
    user_id: str | None,
    task_id: str,
    task_difficulty: str | None,
    is_solved_attempt: bool,
):
    if not user_id:
        return None

    db_user = await uow.users.get(user_id)
    if not db_user:
        return None

    stats = ensure_user_stats(db_user.get("stats"))
    stats["attempts"] = int(stats.get("attempts", 0)) + 1

    task_id_str = str(task_id)
    solved = bool(is_solved_attempt)
    coins_rewarded = 0

    if solved and task_id_str not in stats["solved_task_ids"]:
        stats["solved_task_ids"].append(task_id_str)
        stats["solved_tasks"] = len(stats["solved_task_ids"])
        coins_rewarded = coins_for_difficulty(task_difficulty)
        stats["coins"] = int(stats.get("coins", 0)) + coins_rewarded

    await uow.users.update_stats(user_id, stats)

    stats_out = StatsOut(
        solved=stats.get("solved_tasks", len(stats["solved_task_ids"])),
        attempts=stats.get("attempts", 0),
        streak_days=stats.get("streak_days", 0),
        coins=stats.get("coins", 0),
        solved_task_ids=list(stats["solved_task_ids"]),
    )

    return stats_out, solved, coins_rewarded


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

    user_id = await _resolve_user_id(uow, user, payload.login)

    attempt_id = await uow.attempts.save({
        "task_id": payload.task_id,
        "mode": payload.mode,
        "solution_text": stitched_solution,   # ← сохраняем размеченный текст
        "feedback": fb.model_dump(),
        "score": score,
        "time_spent_sec": payload.time_spent_sec,
        "created_at": now,
        "user_id": user_id,
    })

    is_solved = is_attempt_solved(score, fb)

    stats_result = await _maybe_update_user_stats(
        uow, user_id, payload.task_id, task.difficulty, is_solved
    )

    stats_out: StatsOut | None = None
    coins_rewarded = 0
    if stats_result:
        stats_out, is_solved, coins_rewarded = stats_result

    return AttemptOut(
        id=str(attempt_id),
        task_id=payload.task_id,
        solution_text=stitched_solution,
        feedback=fb,
        score=score,
        created_at=now,
        is_solved=is_solved,
        coins_rewarded=coins_rewarded,
        stats=stats_out,
    )

@router.post("/file", response_model=AttemptOut)
async def create_attempt_file(
    task_id: str,
    login: str | None = Form(None),
    file: UploadFile = File(...),
    uow = Depends(get_uow),
    ocr: VisionOCROpenRouter = Depends(get_ocr),
    llm = Depends(get_llm),
    user = Depends(get_user_opt),
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

    user_id = await _resolve_user_id(uow, user, login)

    attempt_id = await uow.attempts.save({
        "task_id": task_id,
        "mode": "solve",
        "solution_text": stitched_solution,
        "feedback": feedback.model_dump(),
        "score": None,
        "created_at": now,
        "user_id": user_id,
    })

    is_solved = is_attempt_solved(None, feedback)

    stats_result = await _maybe_update_user_stats(
        uow, user_id, task_id, task.difficulty, is_solved
    )

    stats_out: StatsOut | None = None
    coins_rewarded = 0
    if stats_result:
        stats_out, is_solved, coins_rewarded = stats_result

    return AttemptOut(
        id=str(attempt_id),
        task_id=task_id,
        solution_text=stitched_solution,
        feedback=feedback,
        score=None,
        created_at=now,
        is_solved=is_solved,
        coins_rewarded=coins_rewarded,
        stats=stats_out,
    )
