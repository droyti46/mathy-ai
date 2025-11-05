# app/api/schemas/attempt.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

from app.api.schemas.auth import StatsOut
from app.api.schemas.chat import ChatMessage

class Span(BaseModel):
    start: int
    end: int
    message: str = ""
    severity: str = "info"

class Feedback(BaseModel):
    spans: List[List[int]] = Field(default_factory=list, exclude=True)
    spans_detail: List[Span] = Field(default_factory=list)

class AttemptIn(BaseModel):
    task_id: str
    text: str = Field(min_length=15)
    login: Optional[str] = None 

class AttemptOut(BaseModel):
    id: str
    task_id: str
    solution_text: str = ""
    feedback: Feedback
    created_at: str
    is_solved: bool = False
    coins_rewarded: int = 0
    stats: Optional[StatsOut] = None

class TeacherAttemptOut(BaseModel):
    task_id: str
    messages: list[ChatMessage]
    is_solved: bool = False
    coins_rewarded: int = 0
    stats: Optional[StatsOut] = None