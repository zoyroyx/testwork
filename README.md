# Approval Service

A production-ready microservice built with FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, and Docker to manage content approval workflows.

Features strict multi-tenancy isolation, idempotency checks, and a robust state machine with audit logs.

## Prerequisites

* Python 3.11+
* Docker & Docker Compose

## Quick Start (Docker Compose)

To start the database and the application server automatically (which includes running database migrations):

```bash
docker-compose up --build
```

The service will start and listen on `http://localhost:8000`.

## Running Tests

To run automated unit and integration tests using SQLite in-memory:

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run tests using `pytest`:
   ```bash
   pytest tests/ -v
   ```

## Example API Requests

All requests must supply the `X-Mock-Auth` header specifying the user identity, workspace isolation context, and permissions.

### 1. Create an Approval Request

```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/ws_1/approval-requests" \
     -H "Content-Type: application/json" \
     -H "Idempotency-Key: unique-key-123" \
     -H "X-Mock-Auth: {\"user_id\": \"usr_1\", \"workspace_id\": \"ws_1\", \"permissions\": [\"approval:create\"]}" \
     -d '{
       "sourceType": "ARTICLE",
       "sourceId": "art_100",
       "title": "New Blog Post",
       "description": "Please review this article before publishing.",
       "reviewerUserIds": ["usr_2", "usr_3"]
     }'
```

### 2. List Requests in a Workspace

```bash
curl -X GET "http://localhost:8000/api/v1/workspaces/ws_1/approval-requests" \
     -H "X-Mock-Auth: {\"user_id\": \"usr_1\", \"workspace_id\": \"ws_1\", \"permissions\": [\"approval:read\"]}"
```

### 3. Approve a Request

```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/ws_1/approval-requests/{request_id}/approve" \
     -H "Content-Type: application/json" \
     -H "X-Mock-Auth: {\"user_id\": \"usr_2\", \"workspace_id\": \"ws_1\", \"permissions\": [\"approval:decide\"]}" \
     -d '{
       "comment": "Grammar looks perfect, approved!"
     }'
```

### 4. Reject a Request

```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/ws_1/approval-requests/{request_id}/reject" \
     -H "Content-Type: application/json" \
     -H "X-Mock-Auth: {\"user_id\": \"usr_2\", \"workspace_id\": \"ws_1\", \"permissions\": [\"approval:decide\"]}" \
     -d '{
       "reason": "Missing required imagery."
     }'
```

### 5. Cancel a Request

```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/ws_1/approval-requests/{request_id}/cancel" \
     -H "Content-Type: application/json" \
     -H "X-Mock-Auth: {\"user_id\": \"usr_1\", \"workspace_id\": \"ws_1\", \"permissions\": [\"approval:cancel\"]}" \
     -d '{
       "reason": "Accidental submission."
     }'
```