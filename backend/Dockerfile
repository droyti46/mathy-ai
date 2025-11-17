# Multi-stage build для production
FROM python:3.11-slim as builder

WORKDIR /app

# Установка poetry
RUN pip install --no-cache-dir poetry

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock ./

# Настраиваем poetry и устанавливаем зависимости
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-interaction --no-ansi

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Копируем виртуальное окружение из builder
COPY --from=builder /app/.venv /app/.venv

# Копируем приложение
COPY app ./app
COPY data ./data

# Создаем необходимые директории
RUN mkdir -p var/storage

# Устанавливаем переменные окружения
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Открываем порт
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()"

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
