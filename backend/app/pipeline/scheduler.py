from datetime import date, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

scheduler = AsyncIOScheduler()


async def job_pull_lineups():
    from app.pipeline.statcast import get_daily_games
    today = date.today()
    games = await get_daily_games(today)
    print(f"[{datetime.utcnow().isoformat()}] Pulled {len(games)} games for {today}")


async def job_pull_odds():
    from app.pipeline.odds_api import fetch_odds_for_date
    today = date.today()
    odds = await fetch_odds_for_date(today)
    print(f"[{datetime.utcnow().isoformat()}] Pulled {len(odds)} odds entries for {today}")


async def job_run_models():
    print(f"[{datetime.utcnow().isoformat()}] Running models...")


async def job_pull_results():
    print(f"[{datetime.utcnow().isoformat()}] Pulling results...")


def setup_scheduler():
    scheduler.add_job(job_pull_lineups, "cron", hour=6, minute=0, id="pull_lineups")
    scheduler.add_job(job_pull_odds, "cron", hour=7, minute=0, id="pull_odds")
    scheduler.add_job(job_run_models, "cron", hour=8, minute=0, id="run_models")
    scheduler.add_job(job_pull_results, "cron", hour=22, minute=0, id="pull_results")
    scheduler.start()
