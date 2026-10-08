# 🧩 TaskFlow API

A Django RESTful API for managing personal or team tasks — featuring JWT auth, PostgreSQL, Redis, Celery, and Nginx in a Dockerized production setup.

> This is an extended fork of [omidcodes/taskflow-api](https://github.com/omidcodes/taskflow-api). See [What's new in this fork](#-whats-new-in-this-fork) for the additions.

📈 [View Test Coverage Report](https://omidcodes.github.io/taskflow-api/)

---

## 🚀 Features

- ✅ Django 5 + Django REST Framework
- ✅ PostgreSQL database (Dockerized)
- ✅ JWT authentication with per-user task ownership
- ✅ Filtering, search, ordering and pagination
- ✅ Redis as Celery broker and Django cache
- ✅ Cached task statistics endpoint
- ✅ Daily due-date reminder emails via Celery beat
- ✅ Celery task queue for async logging
- ✅ Gunicorn for WSGI-based production serving
- ✅ Nginx reverse proxy for HTTP routing and static file delivery
- ✅ Environment config with `.env` and `python-decouple`
- ✅ Swagger UI for API documentation
- ✅ Docker & Docker Compose for development and deployment
- ✅ Pytest-based testing with coverage reporting

---

## 📁 Project Structure

```
taskflow-api/
├── taskflow_api/           # Django project (with celery.py)
├── tasks/                  # App: models, views, serializers, signals, celery tasks
├── tests/                  # Pytest tests for models, views, celery
├── Dockerfile              # Docker image for Django (Gunicorn inside)
├── docker-compose.yml      # Full stack (Django, DB, Redis, Celery worker + beat, Nginx)
├── nginx.conf              # Nginx config for reverse proxy
├── .env                    # Environment variables
├── logs/                   # Log folder (created if missing)
├── requirements.txt        # Python dependencies
├── run_server.sh           # Start all services in production mode
├── lint-clean.sh           # Format & lint Python code using Ruff
└── pytest.ini              # Pytest configuration
```

---

## ⚙️ Prerequisites

- Python 3.12+
- Docker & Docker Compose
- (Optional) Virtualenv for local development

---

## 📦 Setup Instructions

### 🔧 1. Create Virtual Environment (Optional)
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### 🔧 2. Configure Environment
Copy the `.env.example` file and rename it to `.env` .

---

## 🧪 Development Mode (Local Python)

Run Django and Celery locally. Use Docker for DB & Redis only.

```bash
make dev    # using Makefile to create development envionment
pre-commit install && pre-commit install --hook-type commit-msg -f
python manage.py runserver   # Run Django locally
celery -A taskflow_api worker --loglevel=info  # Start Celery worker
celery -A taskflow_api beat --loglevel=info    # Start scheduler (daily reminders)
```

> Local URLs:
> - API: http://localhost:8000/api/tasks/
> - Docs: http://localhost:8000/docs/

---

## 🧪 Run Tests

### ▶️ Run all tests
```bash
pytest
```

### ▶️ With coverage
```bash
pytest --cov=. --cov-report=term-missing
```

### ▶️ (Optional) HTML Coverage Report
```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in your browser
```

---

## 🧩 Celery Background Logging

When a task is created via API, a background task (`log_task_action`) is triggered:

- Logs to `logs/task_activity.log`
- Format:
```
[2025-09-14 19:45:00] Task #12 ('Example Task') was created via Celery background task.
```

---

## 🏭 Production Mode (Dockerized Full Stack)

### ▶️ Start All Services
```bash
./run_server.sh
```

This command will:
- Build the Docker image
- Run Django with Gunicorn
- Serve via Nginx on port `80`
- Collect static files into a volume
- Expose the full app on http://localhost/

> Alternatively:
```bash
docker compose up --build
```

---

## 🌐 Accessing App

- Web App: [http://localhost/](http://localhost/)
- API: [http://localhost/api/tasks/](http://localhost/api/tasks/)
- Swagger Docs: [http://localhost/docs/](http://localhost/docs/)

---

## 🗃️ Tech Stack

| Layer         | Tech                    |
|---------------|-------------------------|
| Backend       | Django 5 + DRF          |
| Database      | PostgreSQL              |
| Auth          | JWT (SimpleJWT)         |
| Broker/Cache  | Redis                   |
| Async Tasks   | Celery                  |
| Server        | Gunicorn + Nginx        |
| Containers    | Docker Compose          |
| Testing       | Pytest + pytest-cov     |
| Linting       | Ruff                    |
| Deployment    | Shell scripts + volumes |

---

## ✨ What's new in this fork

Extensions added on top of the original project by [Vivashwan Ghosh](https://github.com/Vivashwan):

### 🔐 Authentication & ownership
- JWT auth with SimpleJWT: `POST /api/auth/register/`, `POST /api/auth/token/`, `POST /api/auth/token/refresh/`
- Every task belongs to a user. Users only see their own tasks; another user's task returns `404`, so IDs can't be probed.
- Data migration (`0002`) backfills existing tasks to a `legacy` user before making `owner` NOT NULL, so upgrades don't fail on old data.

### 🔎 Querying
- Filter: `?status=todo`, `?due_after=2026-01-01&due_before=2026-01-31`
- Search title and description: `?search=login`
- Order: `?ordering=due_date` or `?ordering=-created_at`
- Page-number pagination (10 per page)
- Composite indexes on `(owner, status)` and `(owner, due_date)` for the filtered list queries; `select_related` keeps list requests at a fixed query count.

### 📊 Cached stats — `GET /api/tasks/stats/`
```json
{ "total": 4, "by_status": { "todo": 2, "in-progress": 1, "done": 1 }, "overdue": 1, "due_today": 1 }
```
- All counts come from a single aggregate query (`Count` with `filter=Q(...)`).
- Cached per user in Redis for 5 minutes and invalidated by `post_save` / `post_delete` signals, so it never serves stale data.

### ⏰ Due-date reminders
- `send_due_soon_reminders` runs daily at 08:00 via Celery beat and emails each user one digest of unfinished tasks due tomorrow (one query for all tasks and owners).

### 🛠️ Infrastructure fixes
- Switched Celery broker from RabbitMQ to Redis (also used as the cache) and added a `celery-beat` service.
- Fixed the Dockerfile: `apt-get install netcat` failed on `python:3.12-slim` (no `apt-get update`, package renamed to `netcat-openbsd`).
- Re-encoded `requirements.txt` from UTF-16 to UTF-8.
- Added `ruff.toml` and fixed existing lint errors so the CI lint step passes.

### 🧪 Tests
44 pytest tests covering auth, ownership isolation, filters, pagination, query counts, stats caching and invalidation, Celery reminders, and a migrations-in-sync check.

---

## 📜 License

MIT © Omid Hashemzadeh (original project). Fork additions © 2026 Vivashwan Ghosh, also under MIT.