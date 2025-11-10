<h1 align="center">Мати AI 🦆</h1>
<p align="center">Математический тренажер с искусственным интеллектом<br>
Разработан с любовью на конкурс <a href="https://aiijc.com/ru/">AI Challenge 2025</a></p>

<div align="center">
  <img src="img/logo.png" width=500px>

  <img src="img/main-screen.png" width=500px>
</div>

<h2 align="center">Инструкция по запуску</h2>

Клонируйте репозиторий:

```bash
git clone https://github.com/droyti46/mathy-ai.git
```

### Запуск backend:

Перейдите в директорию с бэкендом
```bash
cd backend
```

Установите зависимости
```bash
poetry install
```

Скопируйте .env.example и вставьте в него свой `OPENROUTER_API_KEY`
```bash
Copy-Item .env.example .env
```

Запустите dev-сервер
```bash
poetry run uvicorn app.main:app --reload --port 8000
```

Проверьте, что сервер запустился

```
http://127.0.0.1:8000
```

Вы должны увидеть ответ сервера:

```json
{"title": "Мати AI API", "docs": "/docs", "status": "ok"}
```

### Запуск frontend:

Перейдите в директорию с фронтендом
```bash
cd frontend
```

Установите зависимости
```bash
npm install
```

Скопируйте .env.example
```powershell
Copy-Item .env.example .env
```

Запустите dev-сервер
```bash
npm run dev -- --host --port 3000
```

Если возникнет ошибка, попробуйте ввести команду
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

Готово! Рабочий сервис находится по адресу
```
http://localhost:3000
```

Если ничего не открывается, попробуйте открыть один из `Network` адресов (в консоли будет):

```bash
VITE v5.4.21  ready in 7223 ms

➜  Local:   http://localhost:3000/
➜  Network: http://XXX.XXX.XXX.XXX:3000/
➜  Network: http://XXX.XXX.XXX.XXX:3000/
```