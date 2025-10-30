from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

OPENROUTER_API_KEY: str = "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"
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
OCR_MODEL: str = 'openai/gpt-4o-mini'

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "math-trainer"
    DATA_PATH: str = "data/tasks.csv"
    STORAGE_DIR: str = "var/storage"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///var/app.db"

    # OpenRouter
    OPENROUTER_API_KEY: str = "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"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL_CHECK: str = "openai/gpt-4o-mini"
    LLM_MODEL_HINT: str = "openai/gpt-4o-mini"
    LLM_MODEL_SOLVE: str = "anthropic/claude-3.5-sonnet"
    LLM_MODEL_VISION: str = "openai/gpt-4o-mini"
    OCR_MODEL: str = 'openai/gpt-4o-mini'
    STRICT_JSON: bool = True

    # Auth/JWT
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALG: str = "HS256"
    ACCESS_EXPIRES_MIN: int = 120
    REFRESH_EXPIRES_DAYS: int = 14

    # Teacher mode
    TEACHER_MODE: bool = True

    def ensure_dirs(self):
        Path(self.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
        Path("./var").mkdir(parents=True, exist_ok=True)
        return self
