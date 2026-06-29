# Сервис согласования контента (Approval Service)

Микросервис на базе FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic и Docker для управления процессами согласования контента.

В сервисе реализована строгая изоляция данных (multi-tenancy), проверка идемпотентности запросов и конечный автомат статусов (state machine) с аудитом изменений.

## Требования

* Python 3.11+
* Docker и Docker Compose

## Быстрый старт (через Docker Compose)

Для автоматического запуска базы данных и приложения (включая применение миграций БД):

```bash
docker-compose up --build
```

Сервис запустится и будет доступен по адресу `http://localhost:8000`.

## Запуск тестов

Для запуска автоматических интеграционных и юнит-тестов с использованием SQLite в оперативной памяти:

1. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv .venv
   # В Windows:
   .venv\Scripts\activate
   # В macOS/Linux:
   source .venv/bin/activate
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Запустите тесты с помощью `pytest`:
   ```bash
   pytest tests/ -v
   ```

## Примеры API-запросов

Все запросы должны содержать HTTP-заголовок `X-Mock-Auth`, который определяет пользователя, воркспейс и список его прав.

### 1. Создание заявки на согласование

```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/ws_1/approval-requests" \
     -H "Content-Type: application/json" \
     -H "Idempotency-Key: unique-key-123" \
     -H "X-Mock-Auth: {\"user_id\": \"usr_1\", \"workspace_id\": \"ws_1\", \"permissions\": [\"approval:create\"]}" \
     -d '{
       "sourceType": "ARTICLE",
       "sourceId": "art_100",
       "title": "Новая статья в блог",
       "description": "Пожалуйста, проверьте эту статью перед публикацией.",
       "reviewerUserIds": ["usr_2", "usr_3"]
     }'
```

### 2. Получение списка заявок воркспейса

```bash
curl -X GET "http://localhost:8000/api/v1/workspaces/ws_1/approval-requests" \
     -H "X-Mock-Auth: {\"user_id\": \"usr_1\", \"workspace_id\": \"ws_1\", \"permissions\": [\"approval:read\"]}"
```

### 3. Согласование заявки (Approve)

```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/ws_1/approval-requests/{request_id}/approve" \
     -H "Content-Type: application/json" \
     -H "X-Mock-Auth: {\"user_id\": \"usr_2\", \"workspace_id\": \"ws_1\", \"permissions\": [\"approval:decide\"]}" \
     -d '{
       "comment": "Грамматика отличная, согласовано!"
     }'
```

### 4. Отклонение заявки (Reject)

```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/ws_1/approval-requests/{request_id}/reject" \
     -H "Content-Type: application/json" \
     -H "X-Mock-Auth: {\"user_id\": \"usr_2\", \"workspace_id\": \"ws_1\", \"permissions\": [\"approval:decide\"]}" \
     -d '{
       "reason": "Отсутствуют обязательные изображения."
     }'
```

### 5. Отмена заявки автором (Cancel)

```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/ws_1/approval-requests/{request_id}/cancel" \
     -H "Content-Type: application/json" \
     -H "X-Mock-Auth: {\"user_id\": \"usr_1\", \"workspace_id\": \"ws_1\", \"permissions\": [\"approval:cancel\"]}" \
     -d '{
       "reason": "Создано по ошибке."
     }'
```
