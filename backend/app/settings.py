from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Корень проекта (как у вас)
BASE_DIR = Path(__file__).resolve().parents[2]

# Кандидаты на расположение .env (будут прочитаны по порядку)
ENV_FILES = (
    str(BASE_DIR / ".env"),
    str(BASE_DIR / "backend" / ".env"),
    str(Path(__file__).resolve().parent / ".env"),
    str(Path(".env")),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # App
    APP_NAME: str = Field(default="math-trainer")

    # Пути
    DATA_PATH: Path = Field(default=Path("data/tasks.csv"))
    STORAGE_DIR: Path = Field(default=Path("var/storage"))

    # БД
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///var/app.db")

    # OpenRouter / LLM
    OPENROUTER_API_KEY: str = Field(..., min_length=1)
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")
    LLM_MODEL_CHECK: str = Field(default="google/gemini-2.5-flash")
    LLM_MODEL_ASSISTANT: str = Field(default="google/gemini-2.5-flash")
    LLM_MODEL_SOLVE: str = Field(default="google/gemini-2.5-flash")
    LLM_MODEL_VISION: str = Field(default="google/gemini-2.5-flash")
    OCR_MODEL: str = Field(default="google/gemini-2.5-flash")
    STRICT_JSON: bool = Field(default=True)

    # Auth / JWT
    JWT_SECRET: str = Field(..., min_length=1)
    JWT_ALG: str = Field(default="HS256")
    ACCESS_EXPIRES_MIN: int = Field(default=120)
    REFRESH_EXPIRES_DAYS: int = Field(default=14)

    # Teacher mode
    TEACHER_MODE: bool = Field(default=True)

    # Полезные утилиты
    def ensure_dirs(self) -> "Settings":
        (BASE_DIR / self.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
        (BASE_DIR / "var").mkdir(parents=True, exist_ok=True)
        return self

    @property
    def data_path_abs(self) -> Path:
        return (BASE_DIR / self.DATA_PATH).resolve()

    @property
    def storage_dir_abs(self) -> Path:
        return (BASE_DIR / self.STORAGE_DIR).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings().ensure_dirs()
