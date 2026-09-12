# Crowdfund Engine

A high-concurrency crowdfunding platform API with an interactive dashboard, built with Django REST Framework and PostgreSQL.

## Features

- Campaign and donation models with atomic, race-condition-safe pledge handling
- `select_for_update()` row-level locking inside `transaction.atomic()` blocks to prevent over-funding under concurrent requests
- Business rule enforcement (no pledging to inactive campaigns, amount validation)
- Filterable, searchable, orderable campaign listing via `django-filter`
- Interactive single-page dashboard (Tailwind CSS + vanilla JavaScript) with live progress bars, campaign creation, and pledging
- Environment-isolated configuration — zero hardcoded secrets, PostgreSQL locally with automatic Render deployment support via `DATABASE_URL`

## Tech Stack

- Python, Django, Django REST Framework
- PostgreSQL (via `psycopg[binary]`)
- django-filter
- WhiteNoise + Gunicorn (production-ready static file serving and WSGI server)
- Tailwind CSS (CDN) + vanilla JavaScript frontend

## Setup

```bash
git clone <your-repo-url>
cd crowdfund_engine
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
SECRET_KEY=your-local-secret-key
DEBUG=True
DB_NAME=crowdfund_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the dashboard.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/campaigns/` | List campaigns (supports `?search=`, `?ordering=`, `?is_active=`) |
| POST | `/api/campaigns/` | Create a new campaign |
| GET | `/api/campaigns/<id>/` | Retrieve a single campaign |
| POST | `/api/campaigns/<id>/pledge/` | Pledge/donate to a campaign |

## Design Notes

- **Concurrency safety**: pledges acquire a row-level lock on the campaign (`select_for_update()`) inside an atomic transaction, so two simultaneous donations to the same campaign can't race and corrupt the `raised_amount` total or push it past the target unexpectedly.
- **Denormalized `raised_amount`**: stored directly on the Campaign model rather than always summed live from Donations, keeping campaign listing fast while writes to it remain tightly controlled through the atomic pledge flow.
- **Environment-based configuration**: all secrets and database credentials load via environment variables with local-safe fallbacks — nothing sensitive is hardcoded or committed.