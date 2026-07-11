from datetime import date, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import settings
from app.db.base import async_session
from app.db.models import Game, Prediction, OddsHistory
from app.models.trainer import ModelTrainer
from app.models.predictor import predict_game
from app.simulation.edge_calc import calculate_edge

scheduler = AsyncIOScheduler()
trainer = ModelTrainer()


async def job_pull_lineups():
    from app.pipeline.statcast import get_daily_games
    today = date.today()
    games = await get_daily_games(today)
    async with async_session() as db:
        for g in games:
            exists = await db.execute(
                select(Game).where(
                    Game.home_team == g["home_team"],
                    Game.away_team == g["away_team"],
                    Game.game_date == today,
                )
            )
            if not exists.scalar_one_or_none():
                db.add(Game(**g))
        await db.commit()
    print(f"[{datetime.utcnow().isoformat()}] Pulled {len(games)} games for {today}")


async def job_pull_odds():
    from app.pipeline.odds_api import fetch_odds_for_date
    today = date.today()
    odds = await fetch_odds_for_date(today)
    async with async_session() as db:
        for o in odds:
            db.add(OddsHistory(**o))
        await db.commit()
    print(f"[{datetime.utcnow().isoformat()}] Pulled {len(odds)} odds entries for {today}")


async def job_run_models():
    print(f"[{datetime.utcnow().isoformat()}] Running models...")
    today = date.today()
    async with async_session() as db:
        result = await db.execute(
            select(Game).where(
                Game.game_date == today,
                Game.status == "scheduled",
            )
        )
        games = result.scalars().all()

        for game in games:
            result_data = await predict_game(game.id, trainer, db)
            for pred in result_data.get("predictions", []):
                model_prob = pred["model_probability"]
                db.add(Prediction(
                    game_id=game.id,
                    model_version="v0.1",
                    market=pred["market"],
                    selection=pred["selection"],
                    model_probability=model_prob,
                ))
        await db.commit()
    print(f"[{datetime.utcnow().isoformat()}] Models ran for {len(games)} games")


async def job_pull_results():
    print(f"[{datetime.utcnow().isoformat()}] Pulling results...")


def setup_scheduler():
    scheduler.add_job(job_pull_lineups, "cron", hour=6, minute=0, id="pull_lineups")
    scheduler.add_job(job_pull_odds, "cron", hour=7, minute=0, id="pull_odds")
    scheduler.add_job(job_run_models, "cron", hour=8, minute=0, id="run_models")
    scheduler.add_job(job_pull_results, "cron", hour=22, minute=0, id="pull_results")
    scheduler.start()
