from typing import List, Literal

from pydantic import BaseModel, Field, model_validator

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

    @model_validator(mode="before")
    @classmethod
    def _coerce_message(cls, value: "ChatMessage | str | dict[str, str]"):
        """Allow creating chat messages from plain strings or dicts without a role."""
        if isinstance(value, str):
            return {"role": "user", "content": value}
        if isinstance(value, dict) and "role" not in value and "content" in value:
            return {"role": "user", **value}
        return value

class HintRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list)

class ChatOut(BaseModel):
    messages: List[ChatMessage]