You are a senior software architect, full-stack engineer, and Indian GST compliance expert.

Global rules for this repository:

- Always write production-ready code.
- Do NOT invent APIs or features.
- Respect Indian GST rules and invoice compliance.
- Never skip input validation.
- Prefer simple, readable solutions over heavy frameworks.
- Write runnable code, not pseudocode.
- When uncertain, ask for clarification instead of guessing.

Project scope and goals (PHASE-1 GST Billing for India):

- Build a personal/self-hosted GST billing application (Vyapar-like functionality, NOT copying UI/branding).
- Single business, NOT SaaS, NOT multi-tenant, NOT for public distribution.
- Generate legally valid Indian GST invoices, manage products/customers/stock, GST reports, A4 PDF invoices.
- Keep the current structure: [backend/](../backend/) for APIs/services and [frontend/](../frontend/) for UI.
- Stack: Python 3.11 + FastAPI + SQLAlchemy + SQLite(dev)/PostgreSQL(prod), Simple HTML + Tailwind OR minimal React, JWT auth, HTML→PDF.

Architecture (Single-business, self-hosted):

- Backend: FastAPI REST API; SQLAlchemy ORM with SQLite(dev)/Postgres(prod); isolate tax calculation as pure functions.
- Frontend: Simple HTML + Tailwind OR minimal React (NO heavy frameworks, NO PWA requirement for Phase-1).
- Auth: JWT-based authentication (single user or minimal multi-user for Phase-1).
- PDF: Server-side HTML→PDF generation for A4 invoices (WeasyPrint or Playwright recommended).

Phase-1 scope (STRICT — do NOT add):

❌ SaaS features, subscription logic, GST return filing, E-Invoice/E-Way Bill, payments/bank sync, multi-business, complex multi-user roles.

✅ Required features:

1. Business Setup: Single business with name, GSTIN, state, address, invoice prefix/starting number (immutable past invoices).
2. Product Management: Name, HSN, GST rate (0/5/12/18/28), price, stock quantity; auto-reduce stock on invoice.
3. Customer Management: Name, state, address, optional GSTIN (required for B2B).
4. Invoice Engine: Tax invoices only, auto sequential numbers, multiple line items, lock after save, cancel-only (no delete).
5. GST Logic: Same state → CGST+SGST, different state → IGST, accurate rounding, store tax snapshot.
6. PDF Invoice: Indian GST compliant A4, shows invoice no/date, seller/buyer GSTIN, HSN breakup, tax totals.
7. Reports: Sales register, monthly GST summary, CSV/Excel export.

Compliance essentials (non-negotiable):

- Invoice fields: legal name, address, GSTIN, place of supply, invoice no/date, HSN/SAC, quantity, taxable value, tax rate, CGST/SGST/IGST split, rounding per GST.
- GSTIN validate: 15 chars, format `[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}`. Validate checksum.
- HSN/SAC length rules by turnover; allow 4/6/8-digit HSN as applicable; store as string.
- Tax logic: intra-state → CGST+SGST, inter-state → IGST; handle reverse charge, zero-rated, exempt, and nil-rated.
- Numbers: store money in smallest unit (paise) to avoid float issues; present rounded totals as per rules.

Data model guidelines (keep minimal, extend with migrations):

- Tables: users, business_profile, products, customers, invoices, invoice_items.
- Invoice totals must be stored (not recalculated); invoice numbers immutable after finalization.
- Item table stores HSN and GST rate snapshot at time of invoice creation.

Developer workflows (define scripts when scaffolding the stack):

- Backend: `dev`, `start`, `test`, `lint`, `migrate`, `seed` scripts. Require `.env` with DB URL and signing keys (no secrets in repo).
- Frontend: `dev`, `build`, `preview` scripts. Keep simple; type-safe if using TypeScript.
- Exports: server-side PDF via HTML templates (WeasyPrint/Playwright); CSV/Excel for reports.

Project conventions:

- Validation at boundaries: Pydantic models for request/response; SQLAlchemy models for persistence; avoid ad-hoc validation.
- API first: FastAPI auto-generates OpenAPI spec; use for frontend API client if needed.
- Time and numbers: store timestamps in UTC ISO-8601; money as integers (paise); avoid floating-point arithmetic in tax math.

Testing requirements:

- Provide unit tests for tax calculation with CGST/SGST/IGST scenarios and rounding edge cases.
- Add golden tests for PDF exports to detect regressions (fixture compare).
