# Nexus

The AI-Native Operating System for D2C Brands — built from the "Nexus" PRD
(v1.1, Build Priorities Summary §15). A single conversational shell routes
free-text (or voice) requests to one of five modules — **Onboard**,
**Source**, **Sell**, **Finance & Compliance**, and **Grow** — all reading
and writing a shared `Brand Context` so an action in one module (e.g.
sourcing a SKU) is immediately usable context in the others (it can be
listed on the storefront, its cost feeds the finance dashboard).

This lives alongside the unrelated VHOS healthcare platform and the
AdSaarthi ad-tech platform in this repo as a third self-contained
subproject (`nexus/`).

## What's built vs. deferred

Per the PRD's own Build Priorities Summary (§15), this build covers **P0
in full, plus the cheap P1 win**:

- ✅ **P0 — Shared conversational shell + Brand Context.** A single
  `/api/chat` endpoint classifies intent and routes to a module service;
  every brand's chat history is persisted and auditable. Voice input/output
  uses the browser's native Web Speech API — no backend STT/TTS service
  required, degrading gracefully to text-only where unsupported.
- ✅ **P0 — Onboard.** Brand + founder conversational intake, a document
  vault with add/update/replace/versioning, and a category-aware guided
  checklist.
- ✅ **P0 — Source.** NL sourcing assistant (LLM-backed when
  `NEXUS_ANTHROPIC_API_KEY` is set, deterministic regex parser otherwise) —
  covers product, packaging, and logistics categories as first-class
  citizens per the PRD. Ranked supplier matching (a Fit Score blending
  price/rating/lead-time, never a bare filter grid), RFQ generation, and a
  manual quote-and-accept flow (Phase 1 scope — no first-party supplier
  portal yet).
- ✅ **P0 — Sell.** NL storefront generator (theme + pages from the brand
  profile), catalog pull-through from sourced orders, payment providers
  pre-enabled by default (confirm-and-activate rather than from-scratch
  signup), shipping zones, and a cross-module FAQ/how-to help layer.
- ✅ **P1 — Finance (Phase 1).** A real-time P&L materialized from
  Source/Sell records (never a duplicate manual ledger), and a tax profile
  read directly from the Onboard document vault.
- ⛔ **Not built — Grow (P2), deep Source marketplace (P3).** Explicitly
  out of scope for this pass, same as the PRD's own treatment of the
  reserved Fulfill module: no ad-platform connectors, no first-party
  supplier registration/portal, no escrow. The data model doesn't block
  adding them later.
- ⛔ **Not built — real B2B/Shopify/payment-gateway/GST-filing
  integrations.** Source suppliers are a seeded internal directory (no live
  IndiaMART/Alibaba connector — PRD §13 flags this needs legal/partnership
  review before building). Payment providers and Shopify sync are modeled
  but not wired to live APIs. GST filing is explicitly assist-only per PRD
  §7.5 and isn't attempted here at all — only the real-time dashboard and
  tax profile pull-through are built.

## Stack

- **Backend**: FastAPI + SQLAlchemy, JWT auth, brand-scoped multi-tenancy.
- **Frontend**: React + TypeScript + Vite + Tailwind. Chat-first shell per
  PRD §10.4 ("similar in spirit to a chat-first app with rich inline
  widgets rather than a traditional multi-tab SaaS dashboard"), with
  structured per-module views (Onboard/Source/Sell/Finance) reachable from
  the sidebar for the "show me as a table" power-user fallback (PRD §10.1).
- **Data**: SQLite by default — swap `NEXUS_DATABASE_URL` for Postgres in
  production, no code changes needed.

The app runs **fully offline** with zero external API keys: the sourcing
NL parser and orchestrator's intent classifier both have deterministic
fallbacks (`app/services/nlp/heuristic_parser.py`, keyword-scoring in
`app/services/orchestrator.py`) used automatically when
`NEXUS_ANTHROPIC_API_KEY` isn't set.

## Project layout

```
nexus/
  backend/
    app/
      models/            Brand, FounderProfile, Document(+versions), Checklist,
                          SourcingRequest/Supplier/CatalogItem/Match/RFQ/Quote/
                          SourcedOrder, Store/Product/Channel/ShippingZone/
                          PaymentProvider/Order/HelpContent, LedgerEntry/TaxProfile,
                          ChatMessage
      api/routes/         auth, onboard, source, sell, finance, chat
      services/
        orchestrator.py    Intent classification + routing (PRD §10.1)
        nlp/               Pluggable LLM / heuristic sourcing-request parser
        source_service.py  Fit Score matching, RFQ generation, quote accept
        site_builder.py    NL -> storefront theme/pages generator
        sell_service.py    Store/catalog/payments/demo order generation
        finance_service.py Ledger materialization, P&L, tax profile
        onboard_service.py Checklist seeding, document versioning
      seed.py              Demo data — mirrors the PRD's own §14 scenario
    tests/                 pytest — 34 tests across parser, matching, ledger,
                           orchestrator routing, onboarding, and API flows
  frontend/
    src/
      pages/Chat.tsx        The primary conversational shell + voice I/O
      widgets/ChatWidgets.tsx  Inline structured views rendered in chat bubbles
      pages/{Onboard,SourceList,SourceDetail,Sell,Finance}.tsx  Table/detail
                             fallback views per module
      lib/useVoice.ts        Web Speech API wrapper (STT + TTS)
  docker-compose.yml
```

## Running locally

### Backend

```bash
cd nexus/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m app.seed          # demo data — login demo@nexus.app / demo12345
uvicorn app.main:app --reload --port 8001
```

API docs: http://localhost:8001/docs

Run tests: `pytest -q`

### Frontend

```bash
cd nexus/frontend
npm install
npm run dev
```

App: http://localhost:5174 (Vite proxies `/api` to `localhost:8001`).

### Docker

```bash
cd nexus
docker compose up --build
```

## Configuration

Copy `backend/.env.example` to `backend/.env`. Every value has a safe
development default; see `app/config.py`. The Anthropic key is optional —
see the offline-fallback note above.
