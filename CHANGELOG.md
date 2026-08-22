# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- CSV import with duplicate detection (`dedup_hash`)
- Transaction CRUD with audit log
- Categorization rule engine
- Savings goals with progress tracking
- Full Pandas analytics service
- Pytest suite covering all PRD success criteria
- Docker + Gunicorn production setup

---

## [0.1.0] - 2025-01-01

### Added
- Initial Flask application scaffold
- SQLAlchemy models: `User`, `Transaction`, `Category`, `CategoryRule`, `Goal`, `ImportBatch`, `AuditLog`
- Flask-Migrate integration for schema versioning
- Flask-Login, Flask-WTF (CSRF), rate-limiting configuration
- Base Jinja2 template with Tailwind CSS and Chart.js
- Dashboard, Add Transaction, and Transactions list routes
- Pandas-based `FinanceAnalytics` class: summary, monthly trends, category breakdown, saving opportunities, projections
- `config.py` with `Development`, `Production`, and `Testing` config classes
- Auth blueprint: login, signup, logout, profile routes
