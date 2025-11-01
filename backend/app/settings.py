from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


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
    DATABASE_URL: str = Field(...)

    # OpenRouter
    OPENROUTER_API_KEY: str = Field(...)
    OPENROUTER_BASE_URL: str = Field(...)
    LLM_MODEL_CHECK: str = Field(...)
    LLM_MODEL_HINT: str = Field(...)
    LLM_MODEL_SOLVE: str = Field(...)
    LLM_MODEL_VISION: str = Field(...)
    OCR_MODEL: str = Field("openai/gpt-4o-mini")
    STRICT_JSON: bool = Field(...)

    # Auth/JWT
    JWT_SECRET: str = Field(...)
    JWT_ALG: str = Field(...)
    ACCESS_EXPIRES_MIN: int = Field(...)
    REFRESH_EXPIRES_DAYS: int = Field(...)

    # Teacher mode
    TEACHER_MODE: bool = Field(...)

    def ensure_dirs(self) -> "Settings":
        Path(self.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
        Path("./var").mkdir(parents=True, exist_ok=True)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings().ensure_dirs()
