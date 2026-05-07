# Work Orders API

Production-ready FastAPI application following **Clean Architecture** principles. Async PostgreSQL (asyncpg), JWT auth, Prometheus metrics, and structured logging.

**Full product and technical documentation** (Executive Summary, Architecture, Security, Roles, Deployment, etc.): **[docs/PRODUCT.md](docs/PRODUCT.md)**.

## Project structure

```
app/
├── api/           # HTTP layer: dependencies, router, v1/workorders
├── core/           # Config, logging, security (JWT)
├── domain/         # Entities, enums, repository interface (no framework)
├── usecases/       # Business logic (depends only on domain)
├── infrastructure/ # DB, ORM models, repository impl, observability
└── main.py
```

## Requirements

- Python 3.11+
- PostgreSQL 15+ (or use Docker)

## Setup

1. Copy environment and set values:

   ```bash
   cp .env.example .env
   # Edit .env: DATABASE_URL, SECRET_KEY, etc.
   ```

2. Create a virtualenv and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. **Create the database** if it doesn't exist (PostgreSQL only):

   ```bash
   python scripts/create_db.py
   ```

   If that fails (e.g. password for user `postgres`), create it manually:

   ```bash
   sudo -u postgres psql -c "CREATE DATABASE workorder_db;"
   # or use the database name from your DATABASE_URL
   ```

4. Run migrations (optional; app also creates tables on startup):

   ```bash
   alembic upgrade head
   ```

5. Start the server:

   ```bash
   uvicorn app.main:app --reload
   ```

If you see **"database X does not exist"**, create that database (step 3) then start again.

## Docker

```bash
# Set SECRET_KEY in .env or pass inline
export SECRET_KEY=your-secret-key
docker-compose up --build
```

- **API**: http://localhost:8000  
- **Docs**: http://localhost:8000/docs  
- **Health**: http://localhost:8000/health/live, http://localhost:8000/health/ready  
- **Metrics**: http://localhost:8000/metrics  
- **Prometheus**: http://localhost:9090  
- **Grafana**: http://localhost:3000 (admin / admin)

## API

- `POST /api/v1/workorders` — create (editor only)
- `GET /api/v1/workorders` — list (viewer+)
- `GET /api/v1/workorders/{id}` — get one (viewer+)
- `PATCH /api/v1/workorders/{id}/status` — update status (editor only)

All protected routes require: `Authorization: Bearer <JWT>`.  
Token payload: `sub` (user id), `role` (`viewer` | `editor`), `exp`.

## Status transitions (enforced in use case)

- **PENDING** → IN_PROGRESS, CANCELLED  
- **IN_PROGRESS** → COMPLETED, CANCELLED  
- **COMPLETED** / **CANCELLED** → no transitions  

Invalid transitions return `422` with a domain error message.

## Tests

```bash
DATABASE_URL=postgresql://localhost/test SECRET_KEY=test PYTHONPATH=. pytest tests/ -v
```

Uses SQLite in-memory for the test DB (overridden in `conftest.py`).

### Test all routes (against running server)

With the app running, hit every route and check status codes:

```bash
python scripts/test_routes.py
# or against another host:
python scripts/test_routes.py http://localhost:8000
```

Requires `SECRET_KEY` (and `DATABASE_URL` if not in `.env`) so the script can issue JWTs.

## Checklist (from spec)

- Domain layer has no FastAPI/SQLAlchemy imports  
- Use cases only import from `domain/`  
- Repository interface in `domain/`, implementation in `infrastructure/`  
- JWT guards on the correct routes  
- Status transition rule in use case; API returns 422 on invalid transition  
- `/health/ready` pings the database  
- `/metrics` via prometheus-fastapi-instrumentator  
- Eight tests implemented with async fixtures  
- docker-compose: app, db, prometheus, grafana  
- `.env.example` includes required keys  
