from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field


# ---- то, что ты прислал как пример ----
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
    lessons: List[LessonOut] = Field(default_factory=list)


# ---- вывода теоретического урока ----
class TheoryContentOut(BaseModel):
    theme_id: str
    lesson_id: str
    title: str
    content_md: str


# ---- плоские айдишники для фронта ----
class TheoryIdPair(BaseModel):
    theme_id: str
    lesson_id: str
