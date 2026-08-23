# Technical Requirements Document: Personal Finance Tracker

**Version:** 1.0
**Owner:** [Your Name]
**Status:** Draft
**Based on:** Personal Finance Tracker PRD v1.0
**Last Updated:** August 22, 2026

---

## 1. Architecture Overview

Monolithic Flask application. Not microservices, not a separate frontend SPA talking to a REST API over the network. Reasons:

- Single-user (per the PRD's v1 scope), low traffic, no need for independent scaling of components.
- A monolith is faster to build, easier to debug, and has fewer moving parts to secure. Microservices here would be over-engineering with no payoff — don't let "best practice" language talk you into complexity this app doesn't need.
- If multi-user or higher scale becomes a real requirement later, the app can be split then. Building for hypothetical future scale now is a cost you pay today for a benefit that may never arrive.

**High-level structure:**

```
Browser (HTML/CSS/JS, Jinja2-rendered)
        |
        v
Flask App (routes, business logic, session auth)
        |
        v
SQLAlchemy ORM
        |
        v
SQLite (file-based DB)

Pandas sits inside the Flask app layer — used for
transaction cleaning, categorization, and aggregation,
not as a separate service.
```

---

## 2. Frontend Stack

**Choice:** Server-rendered Jinja2 templates + vanilla JS + Chart.js. No React/Vue/SPA framework.

**Reasoning:**
- The PRD's feature set (dashboard, transaction list, forms) is standard CRUD + charts. An SPA framework adds build tooling, state management, and API-versioning overhead for zero functional gain at this scope.
- Server-rendered pages mean one less layer to keep in sync (no separate frontend/backend API contract to maintain).
- Chart.js is lightweight, has no backend dependency, and covers the bar/line/pie chart needs (category breakdown, monthly trend) directly from PRD 4.3.

**Components:**
- Jinja2 templates for dashboard, transaction list, forms, goal tracking.
- Vanilla JS (or lightweight fetch calls) for inline edit/delete on the transaction list (PRD 4.4) without full page reloads.
- Chart.js rendered client-side from JSON data injected by Flask or fetched from a lightweight internal API endpoint.

**Trade-off to be explicit about:** if this app later needs richer interactivity (drag-drop, live filtering without reload, offline support), a full SPA rewrite is a real cost. That's an acceptable trade for v1 given current scope — flagging it now so it's not a surprise later.

---

## 3. Backend Stack

**Choice:** Python 3.11+, Flask, SQLAlchemy (ORM), Pandas.

**Reasoning:**
- Flask matches what was specified in the app idea; it's minimal, unopinionated, and appropriate for the scope (no need for Django's full-stack overhead — admin panel, ORM lock-in, etc. — when this app doesn't need most of it).
- SQLAlchemy over raw SQL: gives migration support (via Alembic) and reduces injection risk vs. hand-written queries. Raw SQL string-building is where most amateur finance apps introduce SQL injection bugs — don't do that.
- Pandas handles the data cleaning, categorization matching, and aggregation logic described in PRD 4.1–4.3. It should NOT be used as the storage layer (see Section 4) — that's a common mistake that doesn't scale past a few thousand rows and has no transactional safety.

**Key backend modules:**
- `auth/` — session-based login, password hashing
- `transactions/` — import, CRUD, dedup logic
- `categorization/` — rule matching, user rule overrides
- `analytics/` — Pandas aggregation functions feeding the dashboard
- `goals/` — savings goal CRUD and progress calculation

---

## 4. Database

**Choice:** SQLite for v1, with a defined migration path to PostgreSQL if the app ever becomes multi-user or networked.

**Reasoning:**
- SQLite is file-based, zero-config, sufficient for single-user local/low-traffic deployment.
- SQLAlchemy as the ORM layer means switching to PostgreSQL later is a connection-string change plus minor dialect adjustments, not a rewrite — this is the actual reason to use an ORM instead of raw SQL from day one.
- **Do not use SQLite if the app will ever be accessed by concurrent users over a network.** SQLite's write-locking model will cause errors under concurrent writes. This is the single biggest constraint carried over from the PRD's "single-user" assumption — if that assumption changes, this decision must be revisited before launch, not after.

**Schema (core tables):**

| Table | Key Fields |
|---|---|
| `users` | id, email, password_hash, created_at |
| `transactions` | id, user_id, date, description, amount, type (income/expense), category_id, created_at |
| `categories` | id, user_id, name, is_default |
| `category_rules` | id, user_id, keyword, category_id |
| `goals` | id, user_id, name, target_amount, target_date, created_at |

**Indexing:** index `transactions.date` and `transactions.category_id` — these are the columns every dashboard aggregation query filters/groups on. Skipping this is the most common cause of slow dashboards once transaction count grows past a few hundred rows.

---

## 5. Authentication

**Choice:** Flask session-based auth with server-side password hashing (Werkzeug's `generate_password_hash`/`check_password_hash`, bcrypt-backed).

**Reasoning:**
- Even for a "personal" tool, this handles financial data — it should never ship without login, on the assumption someone will eventually deploy it somewhere network-accessible (home server, cloud VM). Skipping auth because "it's just for me" is a decision that ages badly the moment the app is reachable outside localhost.
- Session-based (not JWT) is the right call here: no SPA, no separate API consumers, no need for stateless token auth. JWT would add complexity (token expiry/refresh logic) with no corresponding benefit for a server-rendered app.
- Passwords: never store plaintext or reversible-encrypted. Hash with bcrypt/Werkzeug's default, minimum 12 rounds.

**Not in v1, flag for later:** OAuth/social login, 2FA. Not needed at single-user scope, but if multi-user ships, 2FA should be reconsidered given the data sensitivity (financial transactions).

---

## 6. APIs

Internal-only JSON endpoints (consumed by the app's own frontend JS, not exposed as a public API in v1).

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/transactions` | GET | Filtered/paginated transaction list (PRD 4.4) |
| `/api/transactions/<id>` | PUT/DELETE | Edit/delete a transaction |
| `/api/transactions/import` | POST | CSV upload and parse |
| `/api/dashboard/summary` | GET | Aggregated totals for dashboard (PRD 4.3) |
| `/api/dashboard/trend` | GET | Monthly trend data for charts |
| `/api/goals` | GET/POST | List/create savings goals |
| `/api/goals/<id>/progress` | GET | Progress calculation for a goal (PRD 4.5) |
| `/api/categories/rules` | GET/POST | View/edit categorization rules |

**Reasoning:** these are separated from page routes so the frontend JS can do inline edits (PRD 4.4) and chart rendering without full page reloads, while still keeping the app a monolith — no separate API service, no CORS complexity, no API versioning needed since there's exactly one consumer (this app's own frontend).

**Not included in v1:** public/external API access, API keys for third-party integration. No stated requirement for this in the PRD — don't build it speculatively.

---

## 7. Deployment Plan

**v1 target:** Single-instance deployment — either local (user runs `flask run` on their own machine) or a small cloud VM/container (e.g., a single Docker container on a low-cost host).

**Reasoning:**
- Matches the single-user, low-traffic scope. No load balancer, no horizontal scaling, no orchestration (Kubernetes) — all of that is unjustified cost and complexity at this scale.
- Docker packaging is still worth it even for a single instance: it makes the SQLite file path, dependencies, and environment reproducible, and makes a future move to a hosted platform (Render, Fly.io, a VPS) straightforward.

**Deployment components:**
- Dockerfile: Python base image, install requirements, run via Gunicorn (not Flask's dev server — the dev server is not production-safe and will silently degrade under any real load).
- Gunicorn behind Nginx (or the host platform's equivalent) if deployed to a network-accessible server, to handle TLS termination and static file serving.
- SQLite file stored on a persistent volume — if deployed to a container platform, verify the storage is not ephemeral, or transaction data will be lost on redeploy. This is a real risk with several popular container hosts' default settings.

**Not in v1:** CI/CD pipeline, staging environment, multi-region deployment. Reasonable to add once there's an actual team or actual production traffic — premature for a v1 single-user app.

---

## 8. Security Requirements

This app handles financial transaction data. Treat it accordingly, not as a toy project.

- **Input validation:** server-side validation on every input (CSV parsing, form submissions) — the PRD already flags this, but it's a hard requirement, not optional. Client-side validation is a UX nicety, not a security control.
- **SQL injection:** mitigated by using SQLAlchemy ORM exclusively; no raw string-interpolated SQL queries anywhere in the codebase.
- **Password storage:** bcrypt/Werkzeug hashing, never plaintext, never reversible encryption.
- **Session security:** `SESSION_COOKIE_SECURE=True` and `SESSION_COOKIE_HTTPONLY=True` if deployed over HTTPS; CSRF protection on all state-changing routes (Flask-WTF's CSRF token, or equivalent) — forms and API POST/PUT/DELETE endpoints are all in scope.
- **File upload handling (CSV import):** validate file type and size before parsing; do not trust the file extension alone — validate content. Cap upload size to prevent a trivial denial-of-service via a massive file.
- **HTTPS:** mandatory if deployed anywhere network-accessible. Not optional, not "add later" — financial data over plaintext HTTP is not acceptable at any deployment stage past localhost.
- **Secrets management:** database credentials, `SECRET_KEY` for session signing, etc. via environment variables, never hardcoded or committed to version control.
- **Backup:** since SQLite is a single file with no built-in replication, define a backup routine (scheduled file copy) before this holds any data the user cares about losing.

---

## 9. Technical Decisions Summary (with reasoning)

| Decision | Choice | Why |
|---|---|---|
| Backend framework | Flask | Matches stated stack; minimal overhead for the scope |
| Frontend | Jinja2 + vanilla JS + Chart.js | No SPA complexity justified at this scope |
| Database | SQLite (v1) | Zero-config, sufficient for single-user; migration path to Postgres via SQLAlchemy if scope changes |
| ORM | SQLAlchemy | Injection safety, migration support (Alembic), DB portability |
| Data processing | Pandas | Matches stated stack; correct use is cleaning/aggregation, not storage |
| Auth | Session-based, server-hashed passwords | No SPA/external API consumer to justify JWT complexity |
| API style | Internal JSON endpoints, not public API | Single consumer (own frontend); no stated need for external access |
| Deployment | Single container, Gunicorn + Nginx | Matches single-user scale; avoids premature infra investment |
| Architecture | Monolith | Fewer moving parts, faster to build and secure at this scope |

---

## 10. Risks and Open Technical Questions

1. **SQLite concurrency ceiling.** If the "single-user" assumption from the PRD turns out wrong — even one additional household member using the same instance concurrently — SQLite's write-locking will cause errors. This needs a decision before deployment, not after a bug report.
2. **CSV format fragility.** The PRD flagged this as unresolved. Until a specific bank export format is chosen, the import parser can't be finalized — this blocks real implementation of PRD 4.1, not just a nice-to-have detail.
3. **No CI/CD or automated testing plan specified here.** Given the app handles financial calculations, at minimum the aggregation and categorization logic (Sections 4.2–4.3 of the PRD) need unit tests before this is trusted with real data. This should be added to the plan before, not after, first deployment.

(End of file - total 185 lines)