# app/api/schemas/attempt.py
from pydantic import BaseModel, Field
from typing import List, Optional

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
    text: str
    mode: str = "solve"  # "solve" | "learn"
    time_spent_sec: Optional[int] = None

class AttemptOut(BaseModel):
    id: str
    task_id: str
    # Текст, который фронт будет подсвечивать
    solution_text: str = ""
    feedback: Feedback
    score: Optional[float] = None
    created_at: str
