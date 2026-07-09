from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ad_accounts, analytics, auth, brands, budget, campaigns, content, influencers
from app.config import get_settings
from app.database import Base, engine
from app.models import *  # noqa: F401,F403  (register all models on Base.metadata)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AdSaarthi API",
    description="Unified Advertising & Content Growth Platform for Emerging D2C Brands",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(brands.router)
app.include_router(ad_accounts.router)
app.include_router(analytics.router)
app.include_router(influencers.router)
app.include_router(campaigns.router)
app.include_router(content.router)
app.include_router(budget.router)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": "adsaarthi-api"}
