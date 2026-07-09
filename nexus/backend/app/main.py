from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, finance, onboard, sell, source
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import *  # noqa: F401,F403  (register all models on Base.metadata)
from app.services.help_service import seed_help_content

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_help_content(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Nexus API",
    description="The AI-Native Operating System for D2C Brands",
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
app.include_router(onboard.router)
app.include_router(source.router)
app.include_router(sell.router)
app.include_router(sell.help_router)
app.include_router(finance.router)
app.include_router(chat.router)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": "nexus-api"}
