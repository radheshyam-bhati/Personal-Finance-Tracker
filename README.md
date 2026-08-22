# Personal Finance Tracker

A full-stack personal finance management web application built with Flask, SQLAlchemy, and Pandas. Track income and expenses, import bank CSVs, categorize transactions automatically, visualize spending trends, and manage savings goals — all in one place.

---

## Features

- **Transaction Management** — Manual entry and CSV import with duplicate detection
- **Auto-Categorization** — Keyword-based rules automatically categorize transactions on entry
- **Dashboard & Analytics** — Monthly trends, category breakdowns, and savings projections powered by Pandas
- **Savings Goals** — Create goals with target dates and track progress in real time
- **Audit Log** — Every edit and deletion is recorded for full traceability
- **Security** — CSRF protection, rate limiting, session hardening, and per-user data isolation

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask 3.0 |
| ORM / DB | SQLAlchemy 3.1, SQLite (dev), PostgreSQL-ready |
| Migrations | Flask-Migrate (Alembic) |
| Analytics | Pandas 2.1 |
| Auth | Flask-Login, Werkzeug password hashing |
| Forms / CSRF | Flask-WTF |
| Frontend | Jinja2 templates, Tailwind CSS, Chart.js |
| Server | Gunicorn (production) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/radheshyam-bhati/Personal-Finance-Tracker.git
cd Personal-Finance-Tracker

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and set SECRET_KEY and DATABASE_URL

# 5. Initialize the database
flask db upgrade

# 6. Run the development server
flask run
```

The app will be available at `http://localhost:5000`.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session signing key | `dev-secret-key-change-in-production` |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///finance.db` |
| `FLASK_ENV` | `development` or `production` | `development` |

> **Never commit a real `SECRET_KEY` to version control.** Use `.env` (git-ignored) or your platform's secrets manager.

---

## Project Structure

```
Personal-Finance-Tracker/
├── app/
│   ├── __init__.py          # Extension initialization
│   ├── models.py            # SQLAlchemy models
│   ├── auth/                # Authentication blueprint
│   ├── main/                # Dashboard & core routes
│   ├── transactions/        # Transaction CRUD & CSV import
│   ├── categorization/      # Rule engine
│   ├── goals/               # Savings goals
│   ├── analytics/           # Pandas aggregation services
│   ├── static/              # CSS, JS assets
│   └── templates/           # Jinja2 HTML templates
├── migrations/              # Alembic migration scripts
├── tests/                   # Pytest test suite
├── analytics.py             # Standalone analytics module
├── app.py                   # Application entry point
├── config.py                # Configuration classes
├── requirements.txt
└── .env.example
```

---

## Running Tests

```bash
pytest --cov=app tests/
```

---

## Deployment

```bash
# Production with Gunicorn
gunicorn -w 2 -b 0.0.0.0:8000 "app:create_app()"
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT
