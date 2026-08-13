# Project Management API (layered architecture)

Async FastAPI + PostgreSQL service for managing projects, their documents,
and per-project access sharing between users. JWT-based auth (1 hour expiry)
issued by `POST /login` guards every business endpoint. Strict separation of
concerns.

```
Request -> Router (HTTP)  ->  Service (business rules)  ->  Repository (SQL)  ->  Model
                  ^                    ^                          ^
             validation           domain errors            SQLAlchemy only
             serialization        no HTTP knowledge        no business rules
```

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
# API   -> http://localhost:8000/api/v1
# Docs  -> http://localhost:8000/docs
```

## Quick start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d db          # just Postgres
alembic upgrade head
uvicorn app.main:app --reload
```

## API

| Method | Path                              | Auth | Notes                                              |
|--------|-----------------------------------|------|-----------------------------------------------------|
| POST   | `/auth`                           | -    | Create user (login, password, password_repeat)      |
| POST   | `/login`                          | -    | Log in, returns a JWT (1 hour expiry)                |
| POST   | `/projects`                       | JWT  | Create project; creator becomes the owner            |
| GET    | `/projects`                       | JWT  | List projects accessible to the caller, with docs    |
| GET    | `/project/{id}/info`              | JWT  | Project details, if the caller has access            |
| PUT    | `/project/{id}/info`              | JWT  | Update name/description                              |
| DELETE | `/project/{id}`                   | JWT  | Owner only; deletes project + its documents           |
| GET    | `/project/{id}/documents`         | JWT  | List a project's documents                            |
| POST   | `/project/{id}/documents`         | JWT  | Upload one or more documents (`.pdf`, `.docx`)        |
| GET    | `/document/{id}`                  | JWT  | Download a document                                    |
| PUT    | `/document/{id}`                  | JWT  | Replace a document's file contents                     |
| DELETE | `/document/{id}`                  | JWT  | Delete a document                                       |
| POST   | `/project/{id}/invite?user=login` | JWT  | Owner only; grants `login` access to the project        |

All paths above are relative to `API_V1_PREFIX` (`/api/v1` by default).

## Tests

```bash
createdb app_test    # or: docker compose exec db createdb -U postgres app_test
pytest -v
```

## Layout

| Path                | Responsibility                                            |
|---------------------|-----------------------------------------------------------|
| `app/core/`         | Settings, logging, domain exceptions                      |
| `app/db/`           | Engine, session factory, declarative base                 |
| `app/models/`       | SQLAlchemy ORM entities                                   |
| `app/schemas/`      | Pydantic request/response contracts                       |
| `app/repositories/` | Data access. No business rules, never commits             |
| `app/services/`     | Use cases and business rules. No HTTP                     |
| `app/api/`          | Routers, dependency wiring, domain-error -> HTTP mapping  |
| `alembic/`          | Migrations                                                |
| `tests/`            | API tests + service tests                                 |
