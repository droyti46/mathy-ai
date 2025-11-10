# Math Trainer Backend v3.3 (FastAPI + DDD + OpenRouter + SQLite) — Windows-ready

## Что нового
- Все нужные `__init__.py` добавлены → импорты стабильно работают на Windows / Python 3.13.
- LLM-адаптер без многострочных строк; только обычные кавычки + `\n`.
- Персистентность (SQLite) + авторизация + попытки + OCR через OpenRouter.
- Разметка решений и полный solve выполняются через Qwen3-4B-Thinking-2507 по NScale API.

## Установка (Windows PowerShell)
```powershell
poetry install
Copy-Item .env.example .env
notepad .env   # впишите OPENROUTER_API_KEY=sk-or-... и NSCALE_SERVICE_TOKEN=...
poetry run uvicorn app.main:app --reload --port 8000
# затем откройте http://127.0.0.1:8000/docs
```

## Как подать запрос к LLM в /docs
1) (Опционально) Авторизуйтесь: `POST /api/auth/register` → `POST /api/auth/login` → **Authorize** → `Bearer <access_token>`.
2) Проверка текста: `POST /api/attempts` (укажите `task_id` и `text`).
3) Фото/скан → OCR → проверка: `POST /api/attempts/file` (query `task_id`, form-data `file`).
4) Подсказка без «слива»: `POST /api/tasks/{id}/hint`.
5) Полное решение (teacher mode): `POST /api/tasks/{id}/solve` при `TEACHER_MODE=true`.

## Полезные команды
Очистка кэша и .pyc, если что-то «залипло»:
```powershell
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Include *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue
```

## Переменные .env
- `DATABASE_URL=sqlite+aiosqlite:///var/app.db`
- `OPENROUTER_API_KEY=...`
- `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`
- `LLM_MODEL_CHECK=openai/gpt-4o-mini`
- `LLM_MODEL_ASSISTANT=openai/gpt-4o-mini`
- `LLM_MODEL_SOLVE=anthropic/claude-3.5-sonnet`
- `LLM_MODEL_VISION=openai/gpt-4o-mini`
- `NSCALE_SERVICE_TOKEN=...`
- `NSCALE_BASE_URL=https://inference.api.nscale.com/v1`
- `NSCALE_MODEL_CHECK=qwen/qwen-3-4b-thinking-2507`
- `NSCALE_MODEL_SOLVE=qwen/qwen-3-4b-thinking-2507`
- `STRICT_JSON=true`
- `TEACHER_MODE=true`
- `DATA_PATH=data/tasks.csv`
- `STORAGE_DIR=var/storage`
- JWT-настройки уже заданы дефолтами.
