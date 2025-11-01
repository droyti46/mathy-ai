from __future__ import annotations

from typing import Any, Iterable


def _extract_spans_detail(feedback: Any) -> Iterable[Any]:
    """Возвращает коллекцию spans_detail из feedback (dict или pydantic-модели)."""

    if feedback is None:
        return []

    if hasattr(feedback, "spans_detail"):
        spans_detail = getattr(feedback, "spans_detail")
    elif isinstance(feedback, dict):
        spans_detail = feedback.get("spans_detail")
    else:
        spans_detail = None

    if spans_detail is None:
        return []

    # Pydantic BaseModel может возвращать list[Span] | tuple[...] — приведём к списку.
    if isinstance(spans_detail, (list, tuple)):
        return list(spans_detail)

    try:
        return list(spans_detail)
    except TypeError:
        return []


def is_attempt_solved(score: float | None, feedback: Any) -> bool:
    """
    Определяет, решена ли задача пользователем.

    - Если score есть, то ориентируемся на него (>= 0.99).
    - Если score = None, то считаем задачу решённой, когда в spans_detail нет ни одного отрезка.
    """

    if score is not None:
        return score >= 0.99

    spans_detail = _extract_spans_detail(feedback)
    return len(spans_detail) == 0

