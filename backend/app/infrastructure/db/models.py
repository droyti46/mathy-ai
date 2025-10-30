# app/infrastructure/db/models.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Float, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from datetime import datetime, timezone
from uuid import uuid4
from app.infrastructure.db.base import Base

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def gen_id() -> str:
    return uuid4().hex

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)            # ← добавили default
    login: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)  # ← DateTime

class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)            # ← добавили default
    task_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True, index=True)
    text: Mapped[str] = mapped_column(Text, default="")
    file: Mapped[str | None] = mapped_column(String, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(SQLITE_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc) # ← DateTime
    mode: Mapped[str] = mapped_column(String, default="learn")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_spent_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
