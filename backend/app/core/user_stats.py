from __future__ import annotations

from typing import Dict


def default_user_stats() -> Dict[str, object]:
    return {
        "coins": 0,
        "solved_tasks": 0,
        "solved_task_ids": [],
        "streak_days": 0,
    }


def ensure_user_stats(stats: Dict[str, object] | None) -> Dict[str, object]:
    if not isinstance(stats, dict):
        return default_user_stats()
    out = default_user_stats()
    out.update({k: v for k, v in stats.items() if k in out})
    # Ensure solved_task_ids is always a list of strings
    solved_ids = out.get("solved_task_ids", [])
    if not isinstance(solved_ids, list):
        solved_ids = []
    out["solved_task_ids"] = [str(task_id) for task_id in solved_ids]
    out["solved_tasks"] = int(out.get("solved_tasks", len(out["solved_task_ids"])) or 0)
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

