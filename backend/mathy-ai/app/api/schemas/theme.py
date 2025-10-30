from pydantic import BaseModel
from typing import Optional

class ThemeOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    tasks_count: int = 0
