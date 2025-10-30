from pydantic import BaseModel
from typing import Optional, Literal

Difficulty = Literal["easy","medium","hard"]

class TaskOut(BaseModel):
    id: str
    theme_id: str
    difficulty: Difficulty
    statement_md: str
    source: Optional[str] = None
    tags: list[str] = []

class DailyTaskOut(BaseModel):
    date: str
    task: TaskOut
