<h1 align="center">Мати AI 🦆</h1>
<p align="center">Математический тренажер с искусственным интеллектом<br>
Разработан с любовью на конкурс <a href="https://aiijc.com/ru/">AI Challenge 2025</a></p>

<div align="center">
  <img src="img/logo.png" width=500px>

  <img src="img/main-screen.png" width=500px>
</div>

<h2 align="center">Инструкция по запуску</h2>

### Клонируйте репозиторий:

```bash
git clone https://github.com/droyti46/mathy-ai.git
```

### Запуск backend:

#### 1. Перейдите в директорию с бэкендом
```bash
cd backend
```

#### 2. Установите зависимости
```bash
poetry install
```

#### 3. Скопируйте .env.example
```bash
Copy-Item .env.example .env
```

#### 4. Запустите dev-сервер
```bash
poetry run uvicorn app.main:app --reload --port 8000
```

#### Проверьте, что сервер запустился

```
http://127.0.0.1:8000
```

#### Вы должны увидеть ответ сервера:

```json
{"title": "Мати AI API", "docs": "/docs", "status": "ok"}
```

### Запуск frontend:

#### 1. Перейдите в директорию с фронтендом
```bash
cd frontend
```

#### 2. Установите зависимости
```bash
npm install
```

#### 3. Скопируйте .env.example
```bash
Copy-Item .env.example .env
```

#### 4. Запустите dev-сервер
```bash
npm run dev
```

#### Готово! Рабочий сервис находится по адресу
```
http://localhost:5173
```