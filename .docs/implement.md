# Implementation Plan: Personal Finance Tracker

**Version:** 1.0
**Based on:** PRD v1.0, TRD v1.0, Backend Schema v1.0, Design System v1.0
**Last Updated:** August 22, 2026

---

## How to Use This Plan

Each phase has a single exit criterion: don't move to the next phase until the current one's deliverables are actually done and verified, not just started. Phases are ordered by dependency, not by how interesting the work is — authentication and database come before any UI, because every other phase depends on them existing first. Skipping ahead (e.g., building UI before the schema is implemented) is the most common way these plans slip.

---

## Phase 0: Setup

**Goal:** A running, empty Flask app with the project skeleton in place — nothing functional yet, just the scaffolding.

**Tasks:**
- Initialize repo, `.gitignore` (exclude `.env`, `*.db`, `__pycache__`)
- Set up Python virtual environment, `requirements.txt` (Flask, SQLAlchemy, Pandas, Flask-WTF, Werkzeug, python-dotenv, Gunicorn, pytest)
- Project structure per TRD Section 3 module breakdown (`auth/`, `transactions/`, `categorization/`, `analytics/`, `goals/`)
- `.env.example` file documenting required environment variables (`SECRET_KEY`, `DATABASE_URL`, `FLASK_ENV`) — actual `.env` never committed
- Basic Flask app factory pattern (`create_app()`) so config can differ between dev/test/prod without code changes
- Health-check route (`/health`) returning 200 — confirms the app boots before anything else is built on top of it

**Deliverables:**
- Repo with working `flask run` that serves a placeholder page
- `requirements.txt` locked to specific versions (not open-ended `>=`) — unpinned versions are how a working app breaks six months later for no code reason
- README with setup instructions (clone, venv, install, run)

**Exit criterion:** `flask run` starts with no errors, `/health` returns 200, a new developer could clone and run this in under 10 minutes following the README alone.

---

## Phase 1: Database

**Goal:** Every table from the Backend Schema doc exists, with migrations, and can be created/torn down reliably.

**Tasks:**
- Install and configure Flask-SQLAlchemy + Alembic (Flask-Migrate)
- Implement all models from Backend Schema Section 2 (`users`, `categories`, `transactions`, `category_rules`, `goals`, `import_batches`, `audit_log`) with correct types, constraints, foreign keys exactly as specified — not a rough approximation
- Implement all indexes specified in Section 2 (composite indexes on `(user_id, date)`, `(user_id, category_id)`, `dedup_hash`, etc.) — these are not optional "add later if slow," they're specified because the query patterns are already known
- Seed script: default categories (`is_default = TRUE`) created automatically on user signup
- Write and run the first Alembic migration
- Unit tests: model constraints actually reject bad data (e.g., `goals.target_date <= start_date` is rejected, `transactions.type` outside `income`/`expense` is rejected)

**Deliverables:**
- All models implemented, migration applied to a local SQLite file
- Constraint tests passing (this phase is not done just because the tables exist — it's done when the constraints are proven to hold)

**Exit criterion:** Running the migration on a clean database produces every table, index, and constraint from the schema doc with zero manual SQL patching required afterward.

---

## Phase 2: Authentication

**Goal:** A user can sign up, log in, log out, and every subsequent request is correctly scoped to their `user_id`.

**Tasks:**
- Signup route: email/password form → validate → hash password (bcrypt via Werkzeug) → create user → seed default categories → log in automatically
- Login route: validate credentials → generic error on failure (no user enumeration, per Backend Schema Section 4) → set session
- Logout route: clear session
- Session config: `SESSION_COOKIE_SECURE`, `HTTPONLY`, `SAMESITE='Lax'`, 7-day rolling expiry
- CSRF protection (Flask-WTF) applied globally to all POST/PUT/DELETE routes
- Login rate limiting (5 attempts / 15 minutes per email) — this was flagged as a gap in the schema doc and must be closed here, not deferred again
- Central query-scoping helper/base class that enforces `user_id` filtering on every data-access function (Backend Schema Section 5) — build this now, before any feature route exists to misuse it
- Auth decorator (`@login_required`) applied to every non-public route

**Deliverables:**
- Working signup/login/logout flow
- Automated tests: an authenticated user cannot access another user's data via direct ID manipulation (e.g., requesting `/api/transactions/<id>` belonging to a different user returns 404, not the data)
- Rate limiting verified with a test that trips it

**Exit criterion:** A penetration-style manual test — logged in as User A, attempt to read/edit/delete User B's transactions, goals, and categories by ID — fails every time (returns 404/403), not just for the happy path.

---

## Phase 3: Core UI Shell

**Goal:** The navigable app shell exists — nav bar, page routing, empty states — before any feature logic is wired in.

**Tasks:**
- Implement Nav Bar component (Design System 4.1) — desktop and mobile bottom-tab variants
- Implement base layout template (Jinja2) with the design system's type scale, color tokens as CSS variables, spacing scale
- Route stubs for Dashboard, Transactions, Goals, Rules pages — each renders its empty state (per Design System 6.2 and the app flow doc's empty-state specs)
- Responsive breakpoints implemented and manually verified at 375px, 768px, 1024px+ (per Design System Section 5)
- Focus states and keyboard navigation verified on nav and buttons — accessibility floor, not a later add-on

**Deliverables:**
- Fully navigable shell with correct empty states on every page, no live data yet
- Visual QA pass against the Design System doc's component specs (spacing, colors, hover states match exactly, not approximately)

**Exit criterion:** Every page is reachable, looks correct at all three breakpoints, and matches the design tokens — before a single feature is built on top of it, so feature work isn't also fighting layout bugs.

---

## Phase 4: Main Features

**Goal:** Every Must-have and Should-have feature from the PRD is functional end-to-end.

Build in this order — each depends on the previous:

**4a. Transaction entry & import (PRD 4.1)**
- Manual entry form (Design System 4.5 spec)
- CSV upload + Pandas parsing/cleaning + validation + flagged-row review UI
- Dedup detection using `dedup_hash`
- `import_batches` record created per import, with undo capability

**4b. Categorization (PRD 4.2)**
- Rule-matching logic applied on entry/import
- Rule management UI (add/edit/delete keyword→category rules)
- Uncategorized review queue

**4c. Dashboard & analytics (PRD 4.3)**
- Pandas aggregation functions: totals, category breakdown, monthly trend
- Summary band, category chart, trend chart (Design System 6.1, 6.3)
- Precomputed/cached aggregates if performance testing (Phase 6) shows raw recomputation is too slow — don't optimize before measuring, but don't ignore the TRD's warning either

**4d. Transaction detail view (PRD 4.4)**
- Filterable/sortable/paginated table (Design System 6.2)
- Inline edit/delete with confirmation on delete
- Edits trigger `audit_log` entries and dashboard recalculation

**4e. Savings goals (PRD 4.5)**
- Goal CRUD
- Progress calculation (computed at read time, not stored, per Backend Schema Section 2.5)
- On-track/off-track flagging logic

**4f. Insights (PRD 4.6, Nice-to-have)**
- Threshold-based rule logic on top of existing aggregates — only build this after 4a–4e are solid; it's explicitly lowest priority and depends on all the analytics groundwork already existing

**Deliverables per sub-phase:** working feature, matching its PRD success criteria exactly (e.g., 4a is not done until duplicate detection catches ≥95% of true duplicates on a test CSV, per PRD 4.1's actual stated bar — not just "it seems to work").

**Exit criterion:** every Must-have and Should-have feature from the PRD passes its own stated success criteria against real test data, not just manual eyeballing.

---

## Phase 5: Integrations

**Goal:** Confirm there are, in fact, no external integrations required for v1 — and if any assumption has changed, resolve it now rather than deploying blind.

**Tasks:**
- Confirm no bank API (Plaid, etc.) is required, per PRD's explicit out-of-scope list
- Finalize which CSV export format(s) are actually supported — this was flagged as an open question in the PRD and TRD and cannot remain open past this point; pick at least one real bank/format and test against a real sample export
- If email is needed anywhere (password reset — not currently in the PRD, worth confirming it's truly out of scope before shipping auth without it), decide now

**Deliverables:**
- Written confirmation of the exact CSV format(s) supported, with a real sample file used in tests
- Decision recorded on password reset (in scope or explicitly deferred — don't let this be an accidental gap)

**Exit criterion:** no unresolved "what format/service does this actually talk to" questions remain — this phase exists specifically to close the two open questions carried since the PRD.

---

## Phase 6: Testing

**Goal:** Confidence the app is correct, not just that it runs.

**Tasks:**
- Unit tests: categorization rule matching, dedup hashing, goal progress calculation, aggregation functions (Pandas logic specifically — this is where financial calculation bugs hide, per TRD Section 10's risk #3)
- Integration tests: full flows — signup → import CSV → view dashboard → edit transaction → check goal progress
- Security tests: ownership enforcement (repeat Phase 2's cross-user access tests at full feature scope, not just on the auth layer alone), CSRF token enforcement, SQL injection attempts against form inputs
- Performance tests: dashboard load time with 1,500+ transactions (TRD's stated benchmark: under 2 seconds), transaction list filtering with 5,000+ rows (under 1 second, per PRD 4.4)
- Manual accessibility pass: keyboard-only navigation through every core flow, screen reader spot-check on forms and error states

**Deliverables:**
- Test suite covering all PRD success-criteria numbers explicitly (not just "tests exist" — tests that actually assert the specific thresholds stated in the PRD)
- Performance test results compared against TRD/PRD benchmarks, with fixes applied if any benchmark is missed

**Exit criterion:** every numeric success criterion stated anywhere in the PRD is backed by a passing automated test, not a one-time manual check.

---

## Phase 7: Deployment

**Goal:** The app runs in its target environment (per TRD Section 7), not just on a developer's machine.

**Tasks:**
- Write Dockerfile (Python base image, Gunicorn as the WSGI server — never the Flask dev server in production, per TRD Section 7)
- Configure Gunicorn worker count appropriately for expected load (low, given single-user scope — don't over-provision)
- Set up Nginx (or platform equivalent) for TLS termination if deployed anywhere network-accessible
- Verify persistent storage for the SQLite file survives redeploys (TRD flagged this as a real risk with some container platforms — confirm, don't assume)
- Environment variable configuration on the target platform (`SECRET_KEY`, `DATABASE_URL`)
- Set up a scheduled backup routine for the SQLite file (TRD Section 8) before any real data is stored

**Deliverables:**
- Deployed instance reachable over HTTPS (if network-accessible) with a working login
- Documented backup procedure, tested at least once (restore from a backup, confirm data integrity — an untested backup is not a real backup)

**Exit criterion:** the app survives a redeploy with data intact, and a backup has been restored successfully at least once as a test, not just configured and assumed to work.

---

## Phase 8: Final Polish

**Goal:** Close remaining gaps between the design spec and the built app, and remove anything shipped as a placeholder.

**Tasks:**
- Visual QA against the full Design System doc — every component, every state (hover, focus, disabled, error, empty) checked against spec, not just the happy path
- Copy pass: every error message states what went wrong and how to fix it (per the design system's error-copy standard); no generic "Something went wrong" left in place
- Remove any debug routes, console logs, or placeholder data left from development
- Final review of the two decisions flagged repeatedly through this project: (1) SQLite's single-user assumption still holds at actual deployment, (2) the audit log and rate limiting are actually in place, not scoped out along the way
- Cross-browser check (Chrome, Firefox, Safari at minimum) and the three responsive breakpoints one final time

**Deliverables:**
- Punch list of visual/copy deviations from spec, resolved
- Final sign-off checklist confirming every PRD Must-have and Should-have feature, every TRD security requirement, and every schema-level ownership rule is verifiably in place

**Exit criterion:** nothing in this app is a placeholder, a "temporary" workaround, or an unresolved open question carried over from an earlier document — every open question raised in the PRD, TRD, Backend Schema, and this plan has an explicit resolution on record.

---

## Cross-Phase Dependency Note

Two decisions have been flagged as open across every document produced so far and must be closed no later than Phase 5:
1. **CSV format support** — blocks real implementation of Phase 4a.
2. **Single-user vs. multi-user deployment assumption** — determines whether SQLite (Phase 1's chosen database) is still the right call by the time Phase 7 deployment happens.

Neither should still be open by the time Phase 5 ends. If they are, that's a planning failure, not a technical one.

(End of file - total 220 lines)