# Workorder Service

A production-grade backend microservice built with **FastAPI** that demonstrates clean architecture, REST API design, security, observability, containerization, and CI/CD concepts.

This project was developed as part of a university assignment to design and partially implement a real-world microservice.

---

## 🚀 Features

- Clean Architecture (Domain, Use Cases, Infrastructure, API layers)
- RESTful API with OpenAPI (Swagger)
- JWT-based authentication & role-based authorization
- SQLite persistence using SQLAlchemy
- Structured JSON logging
- Prometheus metrics & health checks
- Docker & Docker Compose support
- GitHub Actions CI pipeline
- Automated tests with pytest

---

## 🧱 Architecture

The project follows **Clean Architecture** principles:
app/
├── api/ # HTTP layer (FastAPI routes, dependencies)
├── core/ # Configuration, logging, security
├── domain/ # Business entities, rules, interfaces
├── usecases/ # Application use cases
├── infrastructure/ # Database, repositories, observability
└── main.py # Application entry point


**Key idea:**  
Business logic is independent of frameworks, databases, and delivery mechanisms.

---

## 🔐 Security

- Authentication via **JWT (Bearer tokens)**
- Role-based authorization:
  - `viewer` → read-only access
  - `editor` → create/update access
- Token expiry and signature validation

Example header:
Authorization: Bearer <JWT_TOKEN>


---

## 📡 API Endpoints

Base URL: `http://127.0.0.1:8000`

| Method | Endpoint | Description |
|------|--------|------------|
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/workorders` | Create work order |
| GET | `/api/v1/workorders` | List work orders |
| GET | `/api/v1/workorders/{id}` | Get work order |
| PATCH | `/api/v1/workorders/{id}/status` | Update status |

Swagger UI: http://127.0.0.1:8000/docs


---

## 📊 Observability

### Logging
- Structured JSON logs
- Request ID tracing
- Request duration logging

### Monitoring
- Prometheus metrics exposed at `/metrics`
- HTTP request counters and latency histograms

---

## 🧪 Testing

Basic automated tests are implemented using **pytest**.

Run tests:
```bash
pytest -q

🐳 Containerization
Docker

A Dockerfile is provided for containerized deployment.

Build & run:
docker build -t workorder-service .
docker run -p 8000:8000 workorder-service
docker-compose up



🔁 CI/CD

The project includes a GitHub Actions workflow:

Runs on every push and pull request

Installs dependencies

Executes automated tests

Workflow file:
.github/workflows/ci.yml



⚙️ Environment Variables

Example .env file:
APP_ENV=dev
APP_NAME=workorder-service
DATABASE_URL=sqlite:///./workorders.db
JWT_SECRET=supersecretkey
JWT_ISSUER=workorder-service
JWT_AUDIENCE=workorder-clients
LOG_LEVEL=INFO


▶️ Running Locally
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload


📚 Technologies Used

Python 3.11

FastAPI

SQLAlchemy

Pydantic

Uvicorn

PyJWT

Prometheus Client

Docker

GitHub Actions

Pytest


🎓 Academic Context

This project was developed to demonstrate:

Software architecture principles

Backend service design

Security fundamentals

Observability and monitoring

CI/CD concepts


👤 Author

Saleem Alhabachi
