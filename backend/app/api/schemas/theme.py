from pydantic import BaseModel, Field
from typing import Optional


class LessonOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    tasks_count: int = 0
    theme_id: Optional[str] = None


class ThemeOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    tasks_count: int = 0
    lessons: list[LessonOut] = Field(default_factory=list)
