# Design System Specification: Personal Finance Tracker

**Version:** 1.0
**Based on:** PRD v1.0, TRD v1.0
**Last Updated:** August 22, 2026

---

## Design Rationale (read before using this doc)

This is a data-legibility problem first, a visual-identity problem second. Users are scanning numbers to make decisions — the design's job is to make amounts, categories, and trends impossible to misread, not to look impressive.

**Signature element:** Every monetary value in the app — dashboard totals, transaction amounts, goal progress — is set in a monospaced font with tabular figures, right-aligned in its column, and color-coded by sign (income vs. expense). This is the one deliberate, consistent device that makes the app feel like a precise ledger rather than a generic dashboard template. It's functional, not decorative: tabular numerals mean a column of amounts always aligns on the decimal, which is the actual reason ledgers have looked this way for centuries.

Everything else in this system is kept quiet and disciplined around that one signature.

---

## 1. Complete Color Palette

| Token | Hex | Usage |
|---|---|---|
| `ink` | `#16231F` | Primary text, dark UI surfaces (nav bar, headers) |
| `paper` | `#F1F3ED` | Primary background — cool off-white with a faint sage undertone, not the standard cream default |
| `paper-raised` | `#FFFFFF` | Card and form backgrounds, sits on top of `paper` |
| `ledger-green` | `#1F6F54` | Primary accent — income, positive balances, primary buttons, links |
| `ledger-green-dark` | `#154C39` | Hover/pressed state for primary accent |
| `brass` | `#B8912A` | Secondary accent — savings goals, progress indicators, highlights |
| `brick` | `#B84C3E` | Expenses, negative balances, destructive actions, error states |
| `brick-dark` | `#8F3A2F` | Hover/pressed state for brick |
| `stone` | `#8B8F87` | Borders, dividers, disabled states, secondary text |
| `stone-light` | `#DADDD5` | Subtle borders, table row dividers |
| `ink-soft` | `#4A554F` | Secondary body text (not full-strength `ink`) |

**Why this palette:** Green and brick-red are already the semantically correct colors for income/expense in financial contexts — using them as the actual brand accent (not just data-viz colors) means the identity and the function reinforce each other instead of fighting. Brass is reserved strictly for goals/progress so it never competes with the income/expense meaning of green and red elsewhere.

**Do not introduce additional accent colors.** Category charts (PRD 4.3) use tints/shades derived from these tokens (see Section 6.3), not a rainbow palette — a 12-color pie chart is harder to read, not easier.

---

## 2. Typography

| Role | Font | Notes |
|---|---|---|
| Display (page/section titles) | **Fraunces** (serif, weight 500–600) | Used only for page-level titles ("Dashboard," "Transactions," "Goals") — never for body copy or UI labels. This is where the one serif accent lives; keep it rare. |
| UI / Body | **Inter** | All labels, navigation, buttons, form fields, paragraph text. Chosen for legibility at small sizes and wide language support. |
| Monetary / Tabular Data | **IBM Plex Mono** | All amounts, transaction tables, dashboard totals, chart axis values. Must use `font-feature-settings: "tnum"` (tabular numerals) everywhere it appears. This is the signature typographic device — never substitute a proportional font for money values. |

**Type scale (px, desktop):**

| Style | Font | Size | Weight | Line height |
|---|---|---|---|---|
| Display Large | Fraunces | 40px | 600 | 1.15 |
| Display Small (section titles) | Fraunces | 28px | 500 | 1.2 |
| Body Large | Inter | 18px | 400 | 1.5 |
| Body Default | Inter | 15px | 400 | 1.5 |
| Body Small / Caption | Inter | 13px | 400 | 1.4 |
| UI Label | Inter | 14px | 500 | 1.3 |
| Monetary Large (dashboard hero totals) | IBM Plex Mono | 36px | 500 | 1.1 |
| Monetary Default (table rows) | IBM Plex Mono | 15px | 400 | 1.4 |
| Monetary Small (secondary figures) | IBM Plex Mono | 13px | 400 | 1.3 |

**Mobile scale:** reduce Display Large to 30px, Monetary Large to 26px, all other sizes unchanged. Never shrink Body Default or Monetary Default below their listed sizes — this is a numbers-reading app on a small screen, legibility takes priority over fitting more on-screen.

---

## 3. Layout Structure & Spacing

**Base unit:** 8px. All padding, margin, and gap values are multiples of 8 (with 4px allowed only for icon-to-label gaps and tight inline spacing).

**Spacing scale:** 4 / 8 / 16 / 24 / 32 / 48 / 64px

**Grid:**
- Desktop (≥1024px): 12-column grid, 24px gutters, max content width 1200px, centered.
- Tablet (768–1023px): 8-column grid, 16px gutters.
- Mobile (<768px): single column, 16px side margins.

**App shell layout (logged-in views):**
```
+----------------------------------------------------+
| Nav Bar (fixed, 64px height)                        |
+--------+---------------------------------------------+
| Side   | Main content area                            |
| Nav    | (Dashboard / Transactions / Goals / Rules)   |
| 220px  |                                               |
| (col-  |                                               |
| lapses |                                               |
| to     |                                               |
| bottom |                                               |
| tab bar|                                               |
| <768px)|                                               |
+--------+---------------------------------------------+
```

**Card spacing:** 24px internal padding on desktop, 16px on mobile. 16px gap between cards in a grid.

**Section rhythm:** 48px vertical spacing between major page sections (e.g., between the summary band and the category breakdown on the dashboard); 24px between related sub-sections within one card.

---

## 4. UI Component Specifications

### 4.1 Navigation Bar

**Context:** Persistent top bar across all logged-in views (Dashboard, Transactions, Goals, Rules).

- **Dimensions:** 64px height, full width, fixed to top (`position: sticky; top: 0`), `z-index: 100`.
- **Background:** `ink` (`#16231F`)
- **Contents (left to right):** App wordmark (Fraunces, 20px, `paper` color) → primary nav links (Dashboard, Transactions, Goals) → right-aligned: import button, user menu.
- **Nav link typography:** Inter, 14px, weight 500, color `stone` (inactive) / `paper` (active). Active link has a 2px `ledger-green` underline, 8px below text.
- **Padding:** 24px horizontal on desktop, 16px on mobile.
- **Hover state (nav links):** color transitions `stone` → `paper` over 120ms ease.
- **Responsive behavior:** Below 768px, primary nav links move to a bottom tab bar (56px height, fixed to viewport bottom, `paper-raised` background, `ink` icons+labels, active tab in `ledger-green`). The top bar on mobile retains only the wordmark and user menu.

### 4.2 Hero Section

**Note:** Two distinct heroes exist in this app — the logged-out landing/marketing hero, and the logged-in dashboard's summary band. Specified separately since they serve different jobs.

**4.2a Landing Page Hero (logged-out)**
- **Dimensions:** min-height 560px desktop, 420px mobile, full width.
- **Background:** `ink`, with a single static SVG line-chart motif (faint, 8% opacity, `ledger-green`) suggesting a trend line — not a stock photo, not a gradient blob.
- **Headline:** Fraunces, 48px (desktop) / 32px (mobile), weight 600, color `paper`. Copy should state what the user controls, not sell a feature list — e.g. "See where your money actually goes," not "The ultimate finance solution."
- **Subhead:** Inter, 18px, weight 400, color `stone`, max-width 480px.
- **CTA:** Primary button (see 4.3), positioned 32px below subhead.
- **Padding:** 96px vertical, 24px horizontal, content centered, max-width 640px for text block.

**4.2b Dashboard Summary Band (logged-in, equivalent "hero" for the app itself)**
- **Dimensions:** auto-height, full width of main content area, ~140px on desktop.
- **Background:** `paper-raised`, 1px `stone-light` border, 12px border radius.
- **Contents:** three stat blocks in a row (Income / Expenses / Net Savings), each: label in Inter 13px `ink-soft`, value in IBM Plex Mono 36px (Monetary Large), color `ledger-green` for income/positive net, `brick` for expenses/negative net.
- **Responsive:** stacks to a single column below 768px, each stat block full width, 16px gap between them.

### 4.3 Call-to-Action Buttons

**Primary button** (e.g., "Add Transaction," "Save Goal")
- **Dimensions:** height 44px, horizontal padding 20px, border-radius 8px.
- **Background:** `ledger-green`. Text: Inter 14px weight 500, `paper`.
- **Hover:** background → `ledger-green-dark`, transition 120ms ease.
- **Active/pressed:** background `ledger-green-dark`, scale(0.98).
- **Disabled:** background `stone-light`, text `stone`, no hover effect, `cursor: not-allowed`.
- **Focus (keyboard):** 2px `ledger-green` outline, 2px offset — required for accessibility, do not remove default focus rings without replacing them.

**Secondary button** (e.g., "Cancel," "Edit Rules")
- Same dimensions as primary. Background transparent, 1px `stone` border, text `ink`.
- **Hover:** border → `ink`, background `stone-light` at 40% opacity.

**Destructive button** (e.g., "Delete Transaction")
- Same dimensions. Background `brick`, text `paper`.
- **Hover:** background → `brick-dark`.
- Always paired with a confirmation step (per PRD 4.4) — the button itself is never the only barrier to deletion.

**Responsive:** buttons remain fixed height at all breakpoints; on mobile, full-width buttons are used in forms and modals (width: 100%), inline buttons in tables/lists stay auto-width.

### 4.4 Cards / Content Blocks

**Standard card** (dashboard stat blocks, category breakdown, goal progress)
- **Dimensions:** border-radius 12px, no fixed height (content-driven), min-width 280px in grid layouts.
- **Background:** `paper-raised`. Border: 1px solid `stone-light`. No drop shadow by default — flat, ledger-like, not skeuomorphic.
- **Padding:** 24px desktop, 16px mobile.
- **Title:** Inter 14px weight 500, `ink-soft`, uppercase, letter-spacing 0.03em (used as a label, not a heading — Fraunces is reserved for page titles only, not card titles).
- **Hover (interactive cards, e.g., category card that drills into transactions):** border color → `ledger-green`, transition 150ms ease. No scale/lift effect — keep it flat and precise.
- **Responsive:** cards reflow from a 3-column grid (desktop) → 2-column (tablet) → 1-column (mobile), 16px gap at all breakpoints.

### 4.5 Forms

**Text input / number input** (transaction entry, goal creation)
- **Dimensions:** height 44px, border-radius 8px, full width of container.
- **Border:** 1px `stone`. Background `paper-raised`. Text: Inter 15px, `ink`.
- **Focus:** border → `ledger-green`, 2px, no default browser outline (replaced by the border change + a subtle `box-shadow: 0 0 0 3px rgba(31,111,84,0.15)`).
- **Error state:** border → `brick`, 2px. Error message below field: Inter 13px, `brick`, with a specific correction instruction (per the docx skill's error-copy standard: state what's wrong and how to fix it, never just "Invalid input").
- **Amount fields specifically:** use IBM Plex Mono (not Inter) even inside form inputs, since these are the same monetary values shown elsewhere — consistency of the signature device matters inside forms too, not just in display views.
- **Labels:** Inter 13px weight 500, `ink-soft`, positioned above the field, 4px gap.
- **Select/dropdown (category picker):** same dimensions and states as text input, with a chevron icon (16px, `stone`) right-aligned, 12px from edge.

**Form layout:** single column on all breakpoints for transaction/goal forms (these are short forms; multi-column adds scanning complexity for no space benefit at this length). 16px vertical gap between fields.

**Submit/Cancel row:** right-aligned on desktop (Cancel then Save, left to right), full-width stacked buttons on mobile (Save on top, Cancel below), 12px gap.

### 4.6 Footer

**Note:** applies to the logged-out landing page only. The logged-in app does not use a marketing-style footer — the bottom of the app is the transaction table or dashboard content itself, with no footer bar, to avoid wasting vertical space in a data-dense interface.

**Landing page footer:**
- **Background:** `ink`. Text: Inter 13px, `stone`.
- **Padding:** 48px vertical, 24px horizontal.
- **Layout:** left: wordmark + one-line description. Right: link columns (Product, Account, Legal) — 3 columns desktop, stacked accordion-free single column on mobile.
- **Links:** Inter 13px, `stone`, hover → `paper`.
- **Bottom row:** copyright line, 1px `ink-soft`-tinted top border, 24px padding-top, centered on mobile.

---

## 5. Responsive Design Considerations

| Breakpoint | Range | Key changes |
|---|---|---|
| Mobile | <768px | Single-column grid, bottom tab nav, stacked forms/buttons, dashboard stat blocks stack vertically |
| Tablet | 768–1023px | 8-column grid, side nav collapses to icons-only (48px wide) with labels on tap/hover |
| Desktop | ≥1024px | Full 12-column grid, side nav expanded (220px), 3-column card grids |

**Non-negotiable across all breakpoints:**
- Monetary values never wrap or truncate — if space is tight, reduce surrounding padding before shrinking or wrapping a number.
- Touch targets minimum 44×44px on mobile (buttons, table row actions, nav items).
- Visible keyboard focus states on every interactive element, at every breakpoint.

---

## 6. Page-Specific Design Guidelines

### 6.1 Dashboard
- Order top to bottom: Summary band (4.2b) → Insights cards (PRD 4.6, if present) → Category breakdown chart → Monthly trend chart → recent transactions preview (5 rows, link to full list).
- Chart colors pull from the palette: `ledger-green` for income/positive trend lines, `brick` for expense/negative, category breakdown uses tint variations of `ledger-green` and `brass` (not arbitrary chart-library default colors).

### 6.2 Transaction List (PRD 4.4)
- Table, not cards — this is the audit view, density matters more than visual flourish here.
- Columns: Date, Description, Category (as a small pill using category-tint colors), Amount (IBM Plex Mono, right-aligned, color-coded green/brick).
- Row hover: background → `stone-light` at 30% opacity. Inline edit/delete icons appear on hover (desktop) or are always visible (mobile, since there's no hover state).
- Empty state (no transactions yet): centered, `stone` icon, Inter 15px message — "No transactions yet. Import a CSV or add one to get started." — with the primary "Add Transaction" button directly below. This is an invitation to act, not just a blank space.

### 6.3 Category Breakdown Chart
- Pie or horizontal bar (bar preferred — easier to compare category sizes precisely than pie wedges, and it's a data-legibility app, not a decorative one).
- Category color assignment: derive from `ledger-green` and `brass` at varying lightness steps, in a fixed, deterministic order (same category always gets the same shade) — never randomly assigned per render.

### 6.4 Goals Page (PRD 4.5)
- Progress bar: track in `stone-light`, fill in `brass`, rounded ends, height 12px.
- Off-track state: fill color shifts to `brick`, with a one-line status message above the bar in `ink-soft` stating the specific gap (e.g., the shortfall and what's driving it), not just a color change alone — color can't be the only signal (accessibility).

(End of file - total 225 lines)