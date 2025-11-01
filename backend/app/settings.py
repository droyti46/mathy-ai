from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
BASE_DIR = Path(__file__).resolve().parents[2]


APP_NAME: str = "math-trainer"
DATA_PATH: str = "data/tasks.csv"
STORAGE_DIR: str = "var/storage"
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            BASE_DIR / ".env",
            BASE_DIR / "backend" / ".env",
            Path(__file__).resolve().parent / ".env",
            Path(".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = Field("math-trainer")
    DATA_PATH: str = Field(...)
    STORAGE_DIR: str = Field(...)

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///var/app.db"
    DATABASE_URL: str = Field(...)

    # OpenRouter
    OPENROUTER_API_KEY: str = "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"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL_CHECK: str = "openai/gpt-4o-mini"
    LLM_MODEL_HINT: str = "openai/gpt-4o-mini"
    LLM_MODEL_SOLVE: str = "anthropic/claude-3.5-sonnet"
    LLM_MODEL_VISION: str = "openai/gpt-4o-mini"
    OCR_MODEL: str = 'openai/gpt-4o-mini'
    STRICT_JSON: bool = True
    OPENROUTER_API_KEY: str = Field(...)
    OPENROUTER_BASE_URL: str = Field(...)
    LLM_MODEL_CHECK: str = Field(...)
    LLM_MODEL_HINT: str = Field(...)
    LLM_MODEL_SOLVE: str = Field(...)
    LLM_MODEL_VISION: str = Field(...)
    OCR_MODEL: str = Field("openai/gpt-4o-mini")
    STRICT_JSON: bool = Field(...)

    # Auth/JWT
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALG: str = "HS256"
    ACCESS_EXPIRES_MIN: int = 120
    REFRESH_EXPIRES_DAYS: int = 14
    JWT_SECRET: str = Field(...)
    JWT_ALG: str = Field(...)
    ACCESS_EXPIRES_MIN: int = Field(...)
    REFRESH_EXPIRES_DAYS: int = Field(...)

    # Teacher mode
    TEACHER_MODE: bool = True
    TEACHER_MODE: bool = Field(...)

    def ensure_dirs(self) -> "Settings":
        Path(self.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
        Path("./var").mkdir(parents=True, exist_ok=True)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings().ensure_dirs()