# AdSaarthi

Unified Advertising & Content Growth Platform for Emerging D2C Brands, built
from the AdSaarthi PRD (v0.1, July 2026). MVP scope per the PRD: unified ad
analytics, an automated campaign-to-creator matching engine with budget bid
recommendations, per-creator content drafting, a guided campaign launch
assistant, an AI content studio, and a rules-based budget optimizer — all
gated behind a mandatory human review checkpoint before any outreach or
spend commitment.

This lives alongside the unrelated VHOS healthcare platform in this repo as
a self-contained subproject (`adsaarthi/`) with its own backend, frontend,
dependencies, and tests.

## Stack

- **Backend**: FastAPI + SQLAlchemy, JWT auth, multi-tenant (brand-scoped)
  data isolation, role-based access (Owner / Marketer / Content Manager).
- **Frontend**: React + TypeScript + Vite + Tailwind, charts via Recharts.
- **Data**: SQLite by default (swap `ADSAARTHI_DATABASE_URL` for Postgres in
  production — no code changes needed, SQLAlchemy handles both).

The app is fully usable **offline**, with no external API keys required:

- Ad platform connectors (`app/services/connectors/`) fall back to a
  deterministic **mock connector** when Meta/Google OAuth credentials
  aren't configured, so the dashboard populates with realistic synthetic
  data immediately.
- Content generation (`app/services/content_generation/`) falls back to a
  **template provider** when `ADSAARTHI_ANTHROPIC_API_KEY` isn't set.

Both are real, swappable interfaces — plug in live credentials via `.env`
and the same code paths call the real Meta Marketing API, Google Ads API,
and Anthropic API.

## Project Layout

```
adsaarthi/
  backend/
    app/
      models/            SQLAlchemy models (Brand, User, AdAccount, AdMetricDaily,
                          Influencer, CampaignBrief, MatchResult, ContentDraft, ...)
      schemas/            Pydantic request/response schemas
      api/routes/         FastAPI routers (auth, brands, ad-accounts, analytics,
                          influencers, campaigns, content, budget)
      services/
        connectors/        Meta / YouTube / mock ad platform connectors
        matching_engine.py Fit Score ranking + budget-constrained bid recommender
        content_generation/ Pluggable LLM / template content providers
        budget_optimizer.py Rules-based paid/influencer/content split advisor
        analytics_service.py ETL normalization, CAC/ROAS, trend alerts, benchmarks
      seed.py             Demo data (brand, 20 influencers, 90 days of ad metrics,
                          one auto-matched campaign)
    tests/                pytest — matching engine, bid recommender, budget
                          optimizer, and API flow tests (23 tests)
  frontend/
    src/
      pages/              Dashboard, Influencer Directory, Campaigns, Content
                          Studio, Budget, Settings
      api/, state/, components/, lib/
  docker-compose.yml
```

## Running locally

### Backend

```bash
cd adsaarthi/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m app.seed          # optional demo data — login demo@adsaarthi.app / demo12345
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

Run tests:

```bash
pytest -q
```

### Frontend

```bash
cd adsaarthi/frontend
npm install
npm run dev
```

App: http://localhost:5173 (Vite proxies `/api` to `localhost:8000` — see
`vite.config.ts`).

### Docker

```bash
cd adsaarthi
docker compose up --build
```

## Configuration

Copy `backend/.env.example` to `backend/.env`. Every value has a safe
development default; see `app/config.py`. Ad platform and Anthropic
credentials are optional (see fallback behavior above).

## What's implemented vs. explicitly deferred

Matches PRD section 5 (Scope) and 10 (Roadmap):

- **In scope (Phase 1 MVP), implemented**: unified analytics dashboard with
  weekly digest text, trend alerts, category benchmarks; influencer
  directory with filters/compare; auto-match engine (Fit Score + bid
  recommender) with mandatory human review; per-creator auto content
  drafting; AI content studio (blog/ad copy/image concept); campaign brief
  builder + pre-launch checklist + brief export; rules-based budget
  optimizer; role-based multi-tenant auth.
- **Explicitly out of scope (per PRD 5.2 / Phase 2+)**: one-click ad
  launch/bid automation, in-platform influencer payments/escrow,
  predictive CAC/LTV modeling, multi-brand agency mode, video generation,
  influencer self-serve opt-in profiles, WhatsApp Business API delivery
  (digest content is composed and logged, not sent).
