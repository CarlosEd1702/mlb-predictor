from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.pipeline.scheduler import setup_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting MLB Predictor API — debug={settings.debug}")
    if settings.odds_api_key:
        print(f"Odds API configured for key ending in ...{settings.odds_api_key[-4:]}")
    else:
        print("WARNING: No ODDS_API_KEY set. Odds data will be unavailable.")
    setup_scheduler()
    print("Scheduler started (jobs: lineups@6am, odds@7am, models@8am, results@10pm)")
    yield
    print("Shutting down MLB Predictor API")


app = FastAPI(
    title="MLB Predictor API",
    description="Backend for MLB Predictor App — predictions, odds, and tracking",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
