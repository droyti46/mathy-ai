from typing import List

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    login: str
    password: str
    name: str | None = None


class LoginIn(BaseModel):
    login: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    login: str
    name: str | None = None


class StatsOut(BaseModel):
    solved: int
    attempts: int
    streak_days: int = 0
    coins: int = 0
    solved_task_ids: List[str] = Field(default_factory=list)
