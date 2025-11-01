from __future__ import annotations

from typing import Dict, Iterable


DEFAULT_USER_STATS = {
    "coins": 0,
    "solved_tasks": 0,
    "solved_task_ids": [],
    "streak_days": 0,
}


def default_user_stats() -> Dict[str, object]:
    """Return a fresh copy of default user statistics."""
    return dict(DEFAULT_USER_STATS)


def ensure_user_stats(stats: Dict[str, object] | None) -> Dict[str, object]:
    if not isinstance(stats, dict):
        return default_user_stats()
    out = default_user_stats()
    out.update({k: v for k, v in stats.items() if k in out})

    solved_ids_raw = out.get("solved_task_ids", [])
    if isinstance(solved_ids_raw, Iterable) and not isinstance(solved_ids_raw, (str, bytes)):
        solved_ids_iterable = solved_ids_raw
    else:
        solved_ids_iterable = []

    solved_ids: list[str] = []
    seen: set[str] = set()
    for task_id in solved_ids_iterable:
        task_id_str = str(task_id)
        if task_id_str not in seen:
            seen.add(task_id_str)
            solved_ids.append(task_id_str)

    out["solved_task_ids"] = solved_ids
    out["solved_tasks"] = int(len(solved_ids))
    out["coins"] = int(out.get("coins", 0) or 0)
    out["streak_days"] = int(out.get("streak_days", 0) or 0)
    return out


def coins_for_difficulty(difficulty: str | None) -> int:
    mapping = {
        "easy": 5,
        "легкий": 5,
        "лёгкий": 5,
        "medium": 10,
        "средний": 10,
        "hard": 15,
        "сложный": 15,
    }
    if not difficulty:
        return 5
    return mapping.get(str(difficulty).strip().lower(), 5)

