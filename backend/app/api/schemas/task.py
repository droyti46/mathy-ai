from pydantic import BaseModel, Field
from typing import Optional, Literal

Difficulty = Literal["easy","medium","hard"]

class TaskOut(BaseModel):
    id: str
    theme_id: str
    theme_title: Optional[str] = None
    name: str
    difficulty: Difficulty
    statement_md: str
    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    lesson_id: Optional[str] = None
    lesson_title: Optional[str] = None

class DailyTaskOut(BaseModel):
    date: str
    task: TaskOut
