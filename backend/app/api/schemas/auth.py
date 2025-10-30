from pydantic import BaseModel


class RegisterIn(BaseModel):
    login: str
    password: str


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


class StatsOut(BaseModel):
    solved: int
    attempts: int
    streak_days: int = 0
