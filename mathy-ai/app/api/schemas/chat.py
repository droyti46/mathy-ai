from pydantic import BaseModel
from typing import List, Literal

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class HintRequest(BaseModel):
    messages: List[ChatMessage] = []

class HintOut(BaseModel):
    messages: List[ChatMessage]
    model: str | None = None
    used_tokens: int | None = None
    hint_type: str | None = None

class SolutionStep(BaseModel):
    title: str
    content_md: str

class SolutionOut(BaseModel):
    steps: list[SolutionStep]
    final_answer_md: str | None = None
