# README.md
# Personal Finance Tracker

A web-based personal finance tool built with Python (Flask) and Pandas. Track income, expenses, and spending habits with monthly trends and saving opportunities.

## Features

- **Transaction Management**: Manual entry and CSV import with duplicate detection
- **Auto-Categorization**: Rule-based keyword matching with custom rules
- **Dashboard Analytics**: Monthly trends, category breakdowns, spending patterns
- **Saving Opportunities**: AI-powered insights on where to save money
- **Savings Goals**: Track progress toward financial targets
- **Responsive Design**: Works on desktop, tablet, and mobile

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Pandas
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Frontend**: Jinja2 templates, Chart.js, Tailwind CSS
- **Authentication**: Flask-Login with bcrypt password hashing

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
```bash
cd /Users/radheshyambhati/Developer/Personal\ Finance\ Tracker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

Visit `http://localhost:5000` in your browser.

## Project Structure

```
app/
├── __init__.py          # Flask app factory
├── config.py            # Configuration classes
├── models.py            # SQLAlchemy models
├── forms.py             # WTForms forms
├── main/                # Main dashboard routes
├── auth/                # Authentication routes
├── transactions/        # Transaction CRUD & import
├── analytics/           # Analytics & charts
├── goals/               # Savings goals
├── categorization/      # Categories & rules
└── templates/           # Jinja2 templates
```

## Development

### Database Migrations

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

### Running Tests

```bash
pytest
```

## Deployment

### Docker

```bash
docker build -t finance-tracker .
docker run -p 5000:5000 finance-tracker
```

### Production Checklist

- Set `FLASK_ENV=production`
- Generate a strong `SECRET_KEY`
- Use PostgreSQL: `DATABASE_URL=postgresql://user:pass@host/db`
- Set `SESSION_COOKIE_SECURE=True`
- Configure HTTPS/TLS
- Set up SQLite backup routine

## License

MIT License