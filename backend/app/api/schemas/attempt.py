# app/api/schemas/attempt.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

from app.api.schemas.auth import StatsOut

class Span(BaseModel):
    start: int
    end: int
    message: str = ""
    severity: str = "info"

class Feedback(BaseModel):
    summary: str = ""
    # ТВОЙ формат подсветки:
    spans: List[List[int]] = Field(default_factory=list)
    # Подробности (для возможных тултипов):
    spans_detail: List[Span] = Field(default_factory=list)

class AttemptIn(BaseModel):
    task_id: str
    text: str = Field(min_length=15)
    mode: str = "solve"  # "solve" | "learn"
    time_spent_sec: Optional[int] = None

    @field_validator("text")
    @classmethod
    def _ensure_min_length(cls, value: str) -> str:
        if len(value.strip()) < 15:
            raise ValueError("Solution must be at least 15 characters long")
        return value

class AttemptOut(BaseModel):
    id: str
    task_id: str
    # Текст, который фронт будет подсвечивать
    solution_text: str = ""
    feedback: Feedback
    score: Optional[float] = None
    created_at: str
    is_solved: bool = False
    coins_rewarded: int = 0
    stats: Optional[StatsOut] = None
