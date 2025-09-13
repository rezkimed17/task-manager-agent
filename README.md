# Task Manager Agent

Local-first, single-user task manager with FastAPI backend, LangGraph agent client, SQLite, and n8n email notifications.

## Repo Layout

```
app/                 # FastAPI app, routers, models, tools
client/              # LangGraph client & agent loop
web/                 # Minimal UI (served at /web)
alembic/             # Database migrations
scripts/             # Seed script
tests/               # Parser, recurrence, planner, e2e
.github/workflows/   # CI pipeline
```

## Build Order

1. Repo layout and env files
2. Database models and migrations
3. FastAPI skeleton and health routes
4. Single-user auth and settings
5. Task CRUD and search
6. Reminder scheduler, in-process
7. MCP tools for task operations
8. LangGraph graph and nodes
9. n8n email workflow and webhook
10. UI, tests, CI, README

## Quick Start

1. Create env
```
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
```

2. Init DB
```
mkdir -p data
alembic upgrade head
python scripts/seed.py
```

3. Run API
```
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Login and use
```
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"user@example.com","password":"change-me"}'

# Create from natural language
TOKEN=... # paste from login
curl -s -X POST http://127.0.0.1:8000/tasks/nl \
  -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"text":"remind me to email Sara tomorrow at 9 #work !high"}'
```

5. Web UI
Open http://127.0.0.1:8000/web and login with the seeded credentials.

6. Agent (LangGraph client)
```
python -m client.agent user@example.com change-me
> plan my week
> remind me to file taxes next Friday 5pm !high #finance
```

## MCP Tools (HTTP)

Exposed under `/mcp/*` for: `create_task`, `update_task/{id}`, `list_tasks`, `search_tasks`, `schedule_reminder`, `send_email_notification`, `import_tasks`, `export_tasks`, `nl_to_task`.

## Security & Privacy

- Single user, bearer token auth; tokens hashed at rest.
- No secrets or PII logged; tokens masked.
- All records scoped by user id.

## Observability

- JSON logs with request ids.
- `/health`, `/ready`, `/metrics` (Prometheus) endpoints.

## Performance & Cost

- GPT-4o via OpenAI with central caps in `app/config.py`.
- Simple caching in client flow and short outputs.
- Dry-run support for write paths via `DRY_RUN=true`.

## n8n Integration

- Start n8n (optional): `docker-compose up -d`
- Set `N8N_WEBHOOK_URL` and `N8N_WEBHOOK_SECRET` in `.env`.
- Workflow outline:
  - Webhook node (POST `${N8N_WEBHOOK_URL}`) expects JSON `{ title, reason }`.
  - E-mail node sends to your address with subject `[Task ${reason}] ${title}`.
  - Optional: add signature verification in a Code node to HMAC-check `X-N8N-Signature` with shared secret.
- App provides `/n8n/callback` with signature verification for round-trips if desired.

## Tests & CI

- Run tests: `pytest -q`
- CI: Ruff, mypy, pytest via GitHub Actions.

## Troubleshooting

- If SQLite errors: ensure `data/` exists and you ran migrations.
- 401 errors: call `/auth/login` and pass `Authorization: Bearer <token>`.
- Date parsing: uses `dateparser`; include times like `tomorrow at 9`.
- FTS search: use `/mcp/search_tasks?q=keyword`.

## Copy-Paste: Local Run

```
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
mkdir -p data
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

