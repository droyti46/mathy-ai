<h1 align="center">Мати AI 🦆</h1>
<p align="center">Математический тренажер с искусственным интеллектом, разработанный с любовью на конкурс <a href="https://aiijc.com/ru/">AI Challenge 2025</a></p>

<div align="center">
  <img src="img/logo.png" width=500px>
  <img src="img/main-screen.png" width=500px>
</div>

## Инструкция по запуску

Клонируйте репозиторий:

```bash
git clone https://github.com/droyti46/mathy-ai.git
```

### Запуск backend:

1. Перейдите в директорию с бэкендом
    ```bash
    cd backend
    ```

2. Установите зависимости
  ```bash
  poetry install
  ```

3. Скопируйте .env.example
  ```bash
  Copy-Item .env.example .env
  ```

4. Запустите dev-сервер
  ```bash
  poetry run uvicorn app.main:app --reload --port 8000
  ```

### Запуск frontend:

1. Перейдите в директорию с фронтендом
    ```bash
    cd frontend
    ```

2. Установите зависимости
  ```bash
  npm install
  ``

3. Скопируйте .env.example
  ```bash
  Copy-Item .env.example .env
  ```

4. Запустите dev-сервер
  ```bash
  npm run dev
  ```

5. Откройте сайт `http://localhost:5173`