# Work Orders API — Product & Technical Documentation

This document covers product vision, architecture, security, deployment, and requirements. For quick setup and commands, see the [README](../README.md).

---

## 1. Executive Summary

The **Work Orders API** is a production-ready, RESTful backend service for managing work orders with role-based access. It provides secure create, read, and status-update operations over HTTP, with JWT authentication, structured logging, and Prometheus metrics. The system is built on **Clean Architecture** and async Python (FastAPI, SQLAlchemy 2, PostgreSQL), making it suitable for integration into larger workflows, internal tools, or customer-facing applications. Deployment is supported via Docker Compose (app, PostgreSQL, Prometheus, Grafana) and standard Python/uvicorn for development.

---

## 2. Product Description and Vision

**Product description**  
A headless API that manages work order lifecycle: creation, listing, retrieval, and status transitions (pending → in progress → completed or cancelled). It is designed to be consumed by frontends, mobile apps, or other services rather than end-users directly.

**Vision**  
- Be the single source of truth for work order state in an organization or product ecosystem.  
- Expose a stable, versioned API (`/api/v1`) with clear authorization rules and auditability (request IDs, logs, metrics).  
- Support extension (e.g. more entities, richer roles, or clearance levels) without breaking existing clients.

---

## 3. Core Features and Capabilities

| Feature | Description |
|--------|-------------|
| **Work order CRUD (subset)** | Create work orders (title, description, creator); list all; get by ID. |
| **Status lifecycle** | Pending → In progress → Completed or Cancelled; invalid transitions rejected with 422. |
| **Role-based access** | **Editor**: create work orders, update status. **Viewer**: list and get only. |
| **JWT authentication** | Bearer tokens with `sub`, `role`, and `exp`; no built-in login UI (tokens issued by your IdP or scripts). |
| **Health & observability** | `/health/live`, `/health/ready` (DB check), `/metrics` (Prometheus), structured JSON logs with request ID. |
| **API documentation** | OpenAPI (Swagger) at `/docs`; ReDoc available. |

---

## 4. Technical Architecture and Infrastructure

**Architecture style**  
- **Clean Architecture**: domain (entities, enums, repository interface) has no framework dependencies; use cases depend only on domain; infrastructure (DB, HTTP) implements interfaces and depends inward.  
- **Layers**: `domain/` → `usecases/` → `infrastructure/` (DB, observability) and `api/` (FastAPI routes, dependencies).

**Infrastructure**  
- **Application**: FastAPI app run by Uvicorn (ASGI).  
- **Database**: PostgreSQL 15 (async driver: asyncpg); optional auto-creation of the target database on startup.  
- **Observability**: Prometheus scrapes `/metrics`; Grafana for dashboards; structlog for JSON logs.  
- **Deployment**: Single app container; separate containers for PostgreSQL, Prometheus, and Grafana (see `docker-compose.yml`).

**High-level flow**  
- HTTP request → middleware (request ID, logging) → route → dependency (JWT, DB session, repository) → use case → repository (domain interface) → DB. Response includes `X-Request-ID`.

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| **Runtime** | Python 3.11+ |
| **Framework** | FastAPI, Uvicorn (ASGI) |
| **Database** | PostgreSQL 15, SQLAlchemy 2 (async), asyncpg; Alembic for migrations |
| **Auth** | JWT (python-jose[cryptography]), HS256 |
| **Config** | pydantic-settings, `.env` |
| **Logging** | structlog (JSON) |
| **Metrics** | prometheus-fastapi-instrumentator, Prometheus, Grafana |
| **Testing** | pytest, pytest-asyncio, httpx; SQLite (in-memory) for tests |
| **Containers** | Docker, Docker Compose |

---

## 6. Security Architecture

- **Authentication**: JWT Bearer in `Authorization` header. Tokens are signed with `SECRET_KEY` (HS256); no refresh flow in-app—issue short-lived tokens or integrate with an IdP.  
- **Secrets**: `SECRET_KEY` and `DATABASE_URL` from environment (e.g. `.env`); not committed. Production should use a secrets manager or platform env.  
- **Transport**: No TLS in-app; terminate SSL at a reverse proxy (e.g. Nginx, cloud LB).  
- **API surface**: All `/api/v1/*` routes require a valid JWT; `/health/*` and `/metrics` are unauthenticated (suitable for load balancers and monitoring).  
- **Input**: Pydantic validates request bodies and path/query params; DB access is parameterized (SQLAlchemy) to reduce injection risk.  
- **Logging**: Avoid logging secrets or full tokens; request IDs support audit correlation.

---

## 7. Role and Authorization Management Model

**Roles**  
- **viewer**: Can list work orders and get a work order by ID.  
- **editor**: All viewer capabilities plus create work orders and update work order status.

**Enforcement**  
- Implemented in `api/dependencies.py`: `get_current_user` (valid JWT → `User` with `sub`, `role`); `require_viewer` and `require_editor` used as FastAPI dependencies on routes.  
- Tokens are issued externally (e.g. `scripts/gen_token.py` or your IdP); the API only validates signature and expiry and reads `role` from the payload (defaulting to `viewer` if missing or invalid).

**Route–role matrix**

| Route | Viewer | Editor |
|-------|--------|--------|
| `GET /api/v1/workorders` | ✓ | ✓ |
| `GET /api/v1/workorders/{id}` | ✓ | ✓ |
| `POST /api/v1/workorders` | ✗ (403) | ✓ |
| `PATCH /api/v1/workorders/{id}/status` | ✗ (403) | ✓ |

Unauthenticated requests to these routes receive **401 Unauthorized**.

---

## 8. Clearance Level System

**Current state**  
The system does **not** implement a separate clearance-level or classification model. Authorization is based solely on the **role** (viewer/editor) in the JWT.

**Possible extension**  
- Add a `clearance` (or similar) claim to the JWT and/or store it per user in your IdP.  
- In the API, restrict access to work orders (or fields) by clearance (e.g. only users with clearance ≥ work order classification can read/update).  
- This would require: domain rules for “clearance level” and comparison logic, repository/query changes to filter by clearance, and dependency guards that enforce clearance in addition to role.

---

## 9. User Experience and Interface

**No built-in UI**  
The product is an API-only service. There is no web UI or mobile app shipped with it.

**Developer and operator experience**  
- **OpenAPI (Swagger) UI** at `/docs`: interactive exploration and testing of all endpoints; supports “Authorize” with a Bearer token.  
- **ReDoc** (if mounted): readable API reference.  
- **Structured logs**: JSON with `request_id`, method, path, status, duration; easier to search and correlate.  
- **Health and metrics**: Operators can check liveness/readiness and scrape Prometheus; Grafana can be used for dashboards.

**Integration UX**  
- REST, JSON, and clear status codes (200, 201, 401, 403, 404, 422).  
- `X-Request-ID` on responses for support and debugging.  
- Any frontend (web, mobile, desktop) or backend service can consume the API using the same contracts.

---

## 10. Installation and Deployment

**Prerequisites**  
- Python 3.11+ (for local run) or Docker (for containerized run).  
- PostgreSQL 15 (or use the Compose stack).  
- `SECRET_KEY` and `DATABASE_URL` (and optional env vars; see `.env.example`).

**Local installation**  
1. Clone the repo; create and activate a virtualenv; install deps: `pip install -r requirements.txt`.  
2. Copy `.env.example` to `.env` and set `DATABASE_URL`, `SECRET_KEY`, etc.  
3. Create the database if needed: `python scripts/create_db.py` (or manually).  
4. Optionally run migrations: `alembic upgrade head`.  
5. Start: `uvicorn app.main:app --reload`.

**Deployment with Docker Compose**  
1. Set `SECRET_KEY` (e.g. in `.env` or export).  
2. Run: `docker-compose up --build`.  
3. App: `http://localhost:8000`; Prometheus: 9090; Grafana: 3000.  
4. Use the same `.env` for `SECRET_KEY`; Compose supplies `DATABASE_URL` for the app service.

**Production considerations**  
- Use a strong `SECRET_KEY` and secure DB credentials.  
- Run DB migrations as a separate step or init job.  
- Put the app behind a reverse proxy (HTTPS, rate limiting, etc.).  
- Restrict access to `/metrics` and Grafana (e.g. firewall or auth).

---

## 11. Integration and Scalability

**Integration**  
- **REST/JSON**: Any HTTP client can call the API; OpenAPI schema supports code generation.  
- **Auth**: Integrate with your IdP (e.g. OAuth2/OIDC) to issue JWTs with `sub` and `role` (and optionally `clearance`).  
- **Downstream**: The API can call other services (not in current codebase); use async HTTP (e.g. httpx) and avoid blocking the event loop.

**Scalability**  
- **Stateless app**: Multiple Uvicorn workers or replicas behind a load balancer; no in-process session state.  
- **Database**: Single PostgreSQL instance in the default setup; scale via connection pooling (SQLAlchemy pool settings), read replicas, or sharding if needed.  
- **Observability**: Prometheus and Grafana scale with the number of targets and retention; structlog is suitable for shipping to a log aggregator (e.g. ELK, Loki).

---

## 12. Competitive Analysis and Differentiation

**Differentiation**  
- **Clean Architecture**: Clear separation of domain, use cases, and infrastructure; easier to test and evolve.  
- **Async-first**: Async I/O for DB and HTTP; good throughput under concurrency.  
- **Observability by default**: Request IDs, structured logs, and Prometheus metrics out of the box.  
- **Explicit lifecycle**: Status transitions enforced in the use case layer with clear 422 responses for invalid changes.  
- **API-first**: No UI lock-in; any client can integrate; OpenAPI for documentation and tooling.

**Comparison**  
- Versus generic CRUD backends: built-in roles, status rules, and health/metrics.  
- Versus heavy workflow engines: lightweight and simple to deploy and operate; no built-in BPMN or complex workflows.

---

## 13. Licensing and Commercial Model

**Current state**  
The codebase does not define a specific license or commercial model in this document. Licensing is determined by the repository’s LICENSE file and your organization’s policy.

**If you add a commercial model**  
- Specify license (e.g. MIT, Apache 2.0, or proprietary).  
- Define commercial terms (e.g. subscription, usage-based, support tiers) and any feature gates (e.g. clearance levels, SSO) as needed.

---

## 14. Technical Requirements

**Runtime**  
- Python 3.11 or newer.  
- PostgreSQL 15+ (or compatible), or SQLite for tests only.

**Environment**  
- `DATABASE_URL`: connection string (PostgreSQL recommended for production).  
- `SECRET_KEY`: used for JWT signing; keep secret and strong.  
- Optional: `ALGORITHM` (default HS256), `ACCESS_TOKEN_EXPIRE_MINUTES`, `LOG_LEVEL`.

**Network**  
- Server listens on configurable host/port (default 8000).  
- Outbound: DB and (if used) Prometheus/Grafana; no mandatory external APIs.

**Resource**  
- Minimal CPU/memory for low traffic; scale workers or replicas and DB resources for higher load.

**Dependencies**  
- See `requirements.txt`; all listed packages are required for run and tests (including pytest, httpx, aiosqlite for tests).

---

*For setup commands, API summary, and tests, see the [README](../README.md).*
