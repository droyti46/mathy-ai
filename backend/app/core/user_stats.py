from __future__ import annotations

from typing import Dict

from app.api.schemas.auth import StatsOut


def default_user_stats() -> Dict[str, object]:
    return {
        "coins": 0,
        "solved_tasks": 0,
        "solved_task_ids": [],
        "streak_days": 0,
        "attempts": 0,
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
    out["attempts"] = int(out.get("attempts", 0) or 0)
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


async def maybe_update_user_stats(
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