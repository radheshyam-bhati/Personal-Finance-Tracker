# Product Requirements Document: Personal Finance Tracker

**Version:** 1.0
**Owner:** [Your Name]
**Status:** Draft
**Last Updated:** August 22, 2026

---

## 1. App Overview

A web-based personal finance tool built with Python (Flask) and Pandas. Users import or manually enter income and expense transactions. The app organizes this data, categorizes spending, and surfaces monthly trends, category breakdowns, and savings opportunities — without needing a bank integration or a subscription service.

The core value is not data entry. It's turning raw transactions into decisions: where money is going, whether spending is trending up or down, and whether the user is on track toward a savings target.

---

## 2. Target Users

- Individuals who track their own finances but find spreadsheets tedious to maintain and visualize.
- People who don't want to link bank accounts to a third-party service (privacy-conscious, or just don't trust Mint/YNAB-style aggregators).
- Users comfortable uploading a CSV export from their bank or entering transactions manually.
- Not aimed at: businesses, multi-user households needing shared budgets, or users needing real-time bank sync.

---

## 3. Problem Statement

Most people who try to track spending either:
1. Give up on manual spreadsheet tracking because it's tedious and has no analysis layer, or
2. Don't want to hand banking credentials to a third-party app.

There's a gap for a lightweight, self-hosted-style tool that takes transaction data (CSV or manual entry), does the categorization and analysis automatically, and shows the user concrete patterns — not just a ledger.

---

## 4. Core Features

### 4.1 Transaction Import & Entry

**Description:** Users can add transactions two ways: upload a CSV file (date, description, amount, optionally category) or enter a transaction manually via a form. The app parses, validates, and stores transactions using Pandas for cleanup (deduplication, date normalization, handling missing fields).

**User Flow:**
1. User clicks "Import" → uploads CSV or clicks "Add Transaction" → fills form (date, description, amount, type: income/expense, category).
2. App validates format (correct date, numeric amount). Invalid rows are flagged and shown to the user for correction, not silently dropped.
3. App checks for duplicate transactions (same date + amount + description) and warns before adding.
4. Data is saved to the backend store.

**Technical Requirements:**
- Flask route to handle file upload (`multipart/form-data`) and manual form POST.
- Pandas for CSV parsing, cleaning, dedup logic.
- Data persistence: start with SQLite (via SQLAlchemy) — a flat CSV/pickle file will not scale past a few thousand transactions and won't support concurrent safe writes.
- Input validation on both client (basic HTML5) and server (required, since client-side can be bypassed).

**Priority:** Must-have

**Success Criteria:**
- User can import a 500-row CSV in under 3 seconds with zero data loss.
- Duplicate detection catches at least 95% of true duplicates in test data.
- Manual entry form rejects malformed input (bad date, non-numeric amount) with a clear error message.

---

### 4.2 Automatic Categorization

**Description:** Transactions are assigned a category (e.g., Groceries, Rent, Utilities, Entertainment) either from a rule-based keyword match on the description (e.g., "Uber" → Transport) or manually overridden by the user. Users can create custom categories.

**User Flow:**
1. On import/entry, the app attempts to auto-assign a category using a keyword-matching ruleset.
2. Uncategorized transactions are flagged in a review queue.
3. User manually assigns or corrects categories from a dropdown.
4. User-corrected categorizations feed back into the ruleset (e.g., if user always recategorizes "Amazon" as Household instead of Shopping, the rule updates for that user).

**Technical Requirements:**
- A configurable rules table (keyword → category) stored per user, editable via UI.
- Fallback category: "Uncategorized" — never silently guess wrong and hide it.
- Pandas `.apply()` or vectorized string matching for rule application at scale.

**Priority:** Must-have

**Success Criteria:**
- At least 70% of transactions auto-categorized correctly out of the box using default rules, measured against a labeled test set.
- User can override any category in 2 clicks or fewer.

---

### 4.3 Spending Analysis Dashboard

**Description:** The main view showing: total income vs. expenses for the selected period, spending broken down by category (chart + table), and month-over-month trend (is spending going up or down, and where).

**User Flow:**
1. User lands on dashboard after login/session start.
2. Default view: current month. User can switch to a custom date range or compare two months.
3. Dashboard shows: summary cards (total income, total expenses, net savings), a category breakdown chart, and a trend line for the past 6–12 months.
4. Clicking a category drills into the transaction list for that category (see 4.4).

**Technical Requirements:**
- Pandas groupby/aggregation for category totals and monthly trends.
- Charting library (Chart.js or Plotly) rendered via Flask template or JSON API endpoint consumed by frontend JS.
- Dashboard should load from precomputed aggregates, not recompute from raw transactions on every page load, once transaction count grows — cache or precompute monthly summaries.

**Priority:** Must-have

**Success Criteria:**
- Dashboard loads in under 2 seconds for a user with 12 months of data (~1,500 transactions).
- Category and trend numbers match a manual spot-check calculation exactly (no rounding/aggregation bugs).

---

### 4.4 Transaction Detail View

**Description:** A filterable, sortable list of all transactions — searchable by description, filterable by category, date range, or amount range. This is the "audit" view when a user wants to know exactly what made up a number on the dashboard.

**User Flow:**
1. User clicks into a category or a "View All Transactions" link.
2. List view with filters (category, date range, min/max amount) and a search box.
3. User can edit or delete individual transactions inline.
4. Edits trigger a recalculation of affected dashboard aggregates.

**Technical Requirements:**
- Server-side pagination for large transaction sets (don't load 5,000 rows into the browser at once).
- Edit/delete actions require confirmation for delete (prevent accidental data loss).

**Priority:** Should-have

**Success Criteria:**
- Filtering/searching returns results in under 1 second for up to 5,000 transactions.
- Editing a transaction updates dashboard numbers on next view without requiring a full re-import.

---

### 4.5 Savings Goal Tracking

**Description:** User sets a savings goal (target amount + target date, or a monthly savings target). The app tracks actual net savings (income − expenses) against that goal and shows progress.

**User Flow:**
1. User creates a goal: name, target amount, target date (or recurring monthly target).
2. Dashboard shows progress bar: current savings rate vs. required rate to hit the goal on time.
3. If the user is falling behind pace, the app flags it — with the category(ies) driving the shortfall (e.g., "Dining Out spending is 40% above your 3-month average").

**Technical Requirements:**
- Goal data model: target amount, start date, target date, linked to net savings calculation from transaction data.
- Simple projection logic: (current savings rate × months remaining) vs. (target amount) to flag on-track/off-track.

**Priority:** Should-have

**Success Criteria:**
- Goal progress percentage is accurate to within rounding error of manual calculation.
- User receives an off-track flag when projected savings falls short of target by more than 10%.

---

### 4.6 Saving Opportunity Insights

**Description:** Beyond raw analysis, the app surfaces specific, actionable observations — e.g., "You spent 25% more on Subscriptions this month than your 6-month average" or "Your top 3 categories account for 70% of expenses."

**User Flow:**
1. Insights generated automatically after each dashboard load or data update, shown as a card list ("Insights" section).
2. Each insight is a plain-language statement, not just a chart.

**Technical Requirements:**
- Rule-based logic on top of Pandas aggregates (percentage change thresholds, category concentration ratios). No ML needed for v1 — don't over-engineer this with a model when a threshold rule does the job and is auditable.

**Priority:** Nice-to-have

**Success Criteria:**
- At least 3 relevant, non-redundant insights generated per month of data, validated against manual review of test datasets.

---

## 5. Technical Requirements (Summary)

- **Backend:** Python, Flask (routing, templates, API endpoints).
- **Data processing:** Pandas for cleaning, aggregation, categorization logic.
- **Storage:** SQLite + SQLAlchemy for v1 (single-user, low concurrency). Plan migration path to PostgreSQL if multi-user is added later.
- **Frontend:** Flask templates (Jinja2) + a charting library (Chart.js/Plotly). No SPA framework needed for v1 scope.
- **Auth:** Basic session-based login if the app will ever hold real financial data — even single-user local tools should not skip this if there's any chance of exposure over a network.
- **Data validation:** Server-side validation is mandatory on all inputs; do not rely on client-side checks alone.

---

## 6. Out of Scope (v1)

- Bank account API integration (Plaid, etc.)
- Multi-user / shared household budgets
- Investment or net-worth tracking
- Mobile app (web-responsive only)
- Bill reminders / recurring payment detection

---

## 7. Open Questions

1. Where does the CSV come from — is it always a bank export, and if so, which bank formats need to be supported? Format variance will directly affect the parsing logic in 4.1.
2. Is this single-user only, or should the data model support multiple users from day one? Retrofitting auth and per-user data isolation later is more expensive than building it in now.
3. What happens to categorization rules when a user has zero transaction history — is there a default global ruleset, or does every new user start from "Uncategorized" for everything?

(End of file - total 196 lines)