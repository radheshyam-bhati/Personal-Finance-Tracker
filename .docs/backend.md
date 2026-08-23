# Backend Schema Document: Personal Finance Tracker

**Version:** 1.0
**Based on:** PRD v1.0, TRD v1.0
**Stack:** Flask, SQLAlchemy ORM, SQLite (v1) → PostgreSQL (migration path)
**Last Updated:** August 22, 2026

---

## 1. Design Principles

- Every table that stores user data carries a `user_id` foreign key. There is no shared/global data except `categories.is_default` seed rows and the base `category_rules` seed set. This is a deliberate multi-user-ready design even though v1 deployment is single-user — see the TRD's open question on this trade-off.
- No table trusts the application layer alone for ownership enforcement. Every query that reads or writes user data filters by `user_id`, and this is enforced at the query-construction layer (see Section 5), not left to developer discipline alone.
- Soft-deletes are not used for transactions (financial records should not silently disappear or reappear from a flag flip — a delete is a delete, tracked via an audit table instead, see Section 2.7).

---

## 2. Tables

### 2.1 `users`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL |
| `password_hash` | VARCHAR(255) | NOT NULL |
| `created_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP, ON UPDATE CURRENT_TIMESTAMP |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE |

**Indexes:** UNIQUE index on `email` (also serves as the login lookup index — this is the single most frequent query against this table, so it must be indexed, not scanned).

**Notes:** `password_hash` stores a bcrypt/Werkzeug hash, never plaintext or reversible encryption (per TRD Section 8). `is_active` supports account deactivation without deleting financial history tied to the account.

---

### 2.2 `categories`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `user_id` | INTEGER | FOREIGN KEY → `users.id`, NOT NULL, ON DELETE CASCADE |
| `name` | VARCHAR(100) | NOT NULL |
| `is_default` | BOOLEAN | NOT NULL, DEFAULT FALSE |
| `created_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**Indexes:** composite index on (`user_id`, `name`) — UNIQUE, since a user should not have two categories with the same name (this would break the categorization UI's dropdown and the dashboard's grouping logic).

**Notes:** `is_default` marks the seed categories (Groceries, Rent, Utilities, Transport, Entertainment, Subscriptions, Uncategorized, etc.) created automatically when a user signs up, per PRD 4.2. Users can add custom categories beyond the defaults but cannot delete `is_default = TRUE` rows if any transaction references them — see cascade rules in Section 3.

---

### 2.3 `transactions`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `user_id` | INTEGER | FOREIGN KEY → `users.id`, NOT NULL, ON DELETE CASCADE |
| `category_id` | INTEGER | FOREIGN KEY → `categories.id`, NULLABLE, ON DELETE SET NULL |
| `date` | DATE | NOT NULL |
| `description` | VARCHAR(500) | NOT NULL |
| `amount` | DECIMAL(12,2) | NOT NULL |
| `type` | VARCHAR(10) | NOT NULL, CHECK (`type` IN ('income', 'expense')) |
| `source` | VARCHAR(20) | NOT NULL, DEFAULT 'manual', CHECK (`source` IN ('manual', 'csv_import')) |
| `import_batch_id` | INTEGER | FOREIGN KEY → `import_batches.id`, NULLABLE |
| `dedup_hash` | VARCHAR(64) | NOT NULL |
| `created_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP, ON UPDATE CURRENT_TIMESTAMP |

**Indexes:**
- Composite index on (`user_id`, `date`) — every dashboard aggregation and the transaction list filter by user and date range; this is the highest-traffic query pattern in the app (TRD Section 4 flagged this).
- Composite index on (`user_id`, `category_id`) — supports category breakdown aggregation.
- Index on `dedup_hash` — supports the duplicate-detection check on import (PRD 4.1) without a full table scan.

**Notes:**
- `amount` uses DECIMAL, not FLOAT — floating-point rounding errors are unacceptable in financial data; this is a correctness requirement, not a style preference.
- `dedup_hash` is a computed hash (e.g., SHA-256) of `user_id + date + amount + normalized_description`, computed at insert time, used to detect duplicates in O(1) index lookup rather than comparing every new row against every existing row.
- `category_id` is nullable and `ON DELETE SET NULL` (not CASCADE) — deleting a category must not delete the transactions that used it; they fall back to "Uncategorized" via application logic, not a hard NULL left unhandled.

---

### 2.4 `category_rules`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `user_id` | INTEGER | FOREIGN KEY → `users.id`, NOT NULL, ON DELETE CASCADE |
| `category_id` | INTEGER | FOREIGN KEY → `categories.id`, NOT NULL, ON DELETE CASCADE |
| `keyword` | VARCHAR(255) | NOT NULL |
| `created_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**Indexes:** composite index on (`user_id`, `keyword`) — this table is scanned on every import/manual entry to auto-categorize (PRD 4.2), so lookup speed matters as the rule count grows.

**Notes:** `ON DELETE CASCADE` on `category_id` is intentional here (unlike `transactions.category_id`) — a rule pointing to a deleted category is meaningless and should not persist as an orphaned row.

---

### 2.5 `goals`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `user_id` | INTEGER | FOREIGN KEY → `users.id`, NOT NULL, ON DELETE CASCADE |
| `name` | VARCHAR(255) | NOT NULL |
| `target_amount` | DECIMAL(12,2) | NOT NULL, CHECK (`target_amount` > 0) |
| `start_date` | DATE | NOT NULL |
| `target_date` | DATE | NOT NULL, CHECK (`target_date` > `start_date`) |
| `created_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP, ON UPDATE CURRENT_TIMESTAMP |

**Indexes:** index on `user_id` — goals are always queried per-user, low volume per user so no composite index needed beyond this.

**Notes:** Progress is not stored — it's computed at read time from `transactions` (net savings within the goal's date range vs. `target_amount`), per PRD 4.5. Storing a derived value here would create a sync problem every time a transaction is added, edited, or deleted.

---

### 2.6 `import_batches`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `user_id` | INTEGER | FOREIGN KEY → `users.id`, NOT NULL, ON DELETE CASCADE |
| `filename` | VARCHAR(255) | NOT NULL |
| `row_count` | INTEGER | NOT NULL |
| `rows_imported` | INTEGER | NOT NULL |
| `rows_flagged` | INTEGER | NOT NULL, DEFAULT 0 |
| `imported_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**Notes:** Not in the original PRD feature list explicitly, but required to make PRD 4.1's "invalid rows are flagged and shown to the user for correction" auditable and undoable — without this table, there's no way to answer "which transactions came from which import" if a user needs to review or bulk-remove a bad import.

---

### 2.7 `audit_log`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `user_id` | INTEGER | FOREIGN KEY → `users.id`, NOT NULL, ON DELETE CASCADE |
| `entity_type` | VARCHAR(50) | NOT NULL, CHECK (`entity_type` IN ('transaction', 'goal', 'category', 'category_rule')) |
| `entity_id` | INTEGER | NOT NULL |
| `action` | VARCHAR(20) | NOT NULL, CHECK (`action` IN ('create', 'update', 'delete')) |
| `previous_value` | TEXT | NULLABLE (JSON-serialized snapshot before the change) |
| `created_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**Notes:** This was not in the PRD or TRD but is a hard requirement I'm adding here: financial data that can be silently deleted or edited with no record is a real risk (accidental deletion, disputed numbers later). This is a minimal audit trail, not a full event-sourcing system — don't over-build it, but don't skip it either.

---

### 2.8 `sessions` (if not using Flask's signed-cookie sessions exclusively)

Flask's default session mechanism (signed cookies via `SECRET_KEY`) requires no database table — session data lives client-side, cryptographically signed, not encrypted. This is sufficient for v1 given the session only needs to hold `user_id` and a CSRF token, per TRD Section 5.

**If server-side session invalidation is required** (e.g., "log out all devices," which is not in the current PRD scope but worth flagging as a likely future request for an app holding financial data), a `sessions` table would be needed:

| Column | Type | Constraints |
|---|---|---|
| `id` | VARCHAR(64) | PRIMARY KEY (random token) |
| `user_id` | INTEGER | FOREIGN KEY → `users.id`, NOT NULL, ON DELETE CASCADE |
| `created_at` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| `expires_at` | DATETIME | NOT NULL |

Not building this in v1 since it's not a stated requirement — flagging it so it's a deliberate omission, not an oversight.

---

## 3. Relationships Summary

```
users (1) ──< (many) categories
users (1) ──< (many) transactions
users (1) ──< (many) category_rules
users (1) ──< (many) goals
users (1) ──< (many) import_batches
users (1) ──< (many) audit_log

categories (1) ──< (many) transactions        [ON DELETE SET NULL]
categories (1) ──< (many) category_rules      [ON DELETE CASCADE]

import_batches (1) ──< (many) transactions    [ON DELETE: see below]
```

**Cascade rule for `import_batches` → `transactions`:** deleting an import batch does NOT cascade-delete its transactions by default — that would let a single accidental click destroy months of financial records. "Undo import" must be an explicit, confirmed action in the application layer that deletes the batch's transactions individually and writes to `audit_log`, not a database-level cascade.

**Deleting a `category` with `is_default = TRUE`:** blocked at the application layer if any transaction still references it — the API must return an error directing the user to reassign those transactions first, not silently orphan them or cascade-delete financial records because a category was removed.

---

## 4. Authentication & Session Handling

- **Mechanism:** Flask session-based auth, signed cookies (`SECRET_KEY`-signed, not encrypted — do not put sensitive data directly in the session payload beyond `user_id` and a CSRF token).
- **Password hashing:** Werkzeug's `generate_password_hash` (bcrypt-backed), minimum 12 rounds, per TRD Section 5.
- **Login flow:** POST `/login` with email/password → verify hash → set `session['user_id']` → redirect to dashboard. Failed attempts return a generic "Invalid email or password" (never reveal whether the email exists — that's a user enumeration vulnerability).
- **Session cookie flags:** `SESSION_COOKIE_SECURE=True` (HTTPS only, in any non-local deployment), `SESSION_COOKIE_HTTPONLY=True` (no JS access), `SESSION_COOKIE_SAMESITE='Lax'`.
- **Session expiry:** 7-day rolling expiry on the signed cookie (`PERMANENT_SESSION_LIFETIME`). No "remember me" distinction in v1 — not a stated requirement, don't build it speculatively.
- **CSRF protection:** Flask-WTF CSRF token required on all state-changing routes (POST/PUT/DELETE) — forms and the internal JSON API endpoints alike.
- **Rate limiting on login:** not specified in the PRD/TRD but required — cap failed login attempts (e.g., 5 per 15 minutes per email) to prevent credential-stuffing. This is a gap in the earlier docs that needs to be closed before this ships anywhere network-accessible.

---

## 5. Permissions & Data Ownership Rules

**Core rule:** a user can only ever read, update, or delete rows where `user_id` matches their own session's `user_id`. This is not optional per-endpoint logic — it must be enforced as a single, shared query-scoping layer (e.g., a base query helper or SQLAlchemy query class that automatically filters by `user_id`), so that no individual route can accidentally forget the filter and leak another user's data.

**Enforcement pattern (not endpoint-by-endpoint checks):**
```python
# Every data-access function takes the authenticated user_id
# and the ORM layer enforces the filter centrally, e.g.:
def get_transaction(transaction_id, user_id):
    return Transaction.query.filter_by(
        id=transaction_id, user_id=user_id
    ).first_or_404()
```
A route that queries `Transaction.query.get(id)` without the `user_id` filter is a direct data-leak bug — this pattern must be enforced in code review or via a lint rule, not left to individual developer memory.

**Ownership rules by table:**

| Table | Who can read | Who can write |
|---|---|---|
| `users` | Self only (own profile) | Self only (own profile, password change) |
| `categories` | Owner only | Owner only; `is_default` rows are seeded at signup, not editable in name by the user in v1 (custom categories can be added/renamed freely) |
| `transactions` | Owner only | Owner only |
| `category_rules` | Owner only | Owner only |
| `goals` | Owner only | Owner only |
| `import_batches` | Owner only | Owner only (created by import action, not directly editable) |
| `audit_log` | Owner only, read-only | System-written only, never user-editable |

**No admin role exists in v1.** The PRD does not specify a multi-tenant admin function, and adding one now would be speculative scope — if this becomes a real requirement later, it needs its own access-control design (admin actions would need their own audit trail distinct from user actions), not a quick permissions flag bolted onto the existing model.

---

## 6. Migration Path Note (SQLite → PostgreSQL)

All `DECIMAL(12,2)` and `DATETIME` types map directly to PostgreSQL equivalents (`NUMERIC(12,2)`, `TIMESTAMP`) with no logic changes required, since SQLAlchemy abstracts the dialect difference. The one thing that will need real attention at migration time: SQLite's relaxed type enforcement (it doesn't strictly enforce column types the way Postgres does) means any data that slipped in slightly malformed under SQLite could fail a Postgres import. Run a data validation pass before migrating, don't assume a clean `pg_dump`-style transfer.

(End of file - total 233 lines)