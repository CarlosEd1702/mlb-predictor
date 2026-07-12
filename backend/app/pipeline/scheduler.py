import asyncio
import os
from datetime import date, datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import settings
from app.db.base import async_session
from app.db.models import Game, Prediction, OddsHistory, ModelVersion
from app.models.trainer import ModelTrainer
from app.models.predictor import predict_game
from app.simulation.edge_calc import calculate_edge

scheduler = AsyncIOScheduler()
trainer = ModelTrainer()

TESTSPRITE_NODE = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    r"npm-cache\_npx\8ddf6bea01b2519d\node_modules\@testsprite\testsprite-mcp\dist\index.js",
)
TESTSPRITE_API_KEY = os.environ.get("TESTSPRITE_API_KEY", settings.testsprite_api_key or "")


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

    active_trainer = ModelTrainer.load()
    model_version = "v0.1"

    async with async_session() as db:
        result = await db.execute(
            select(ModelVersion).where(
                ModelVersion.is_active == True,
            ).limit(1)
        )
        active_ver = result.scalar_one_or_none()
        if active_ver:
            model_version = active_ver.version_label

        result = await db.execute(
            select(Game).where(
                Game.game_date == today,
                Game.status == "scheduled",
            )
        )
        games = result.scalars().all()

        for game in games:
            result_data = await predict_game(game.id, active_trainer, db)
            for pred in result_data.get("predictions", []):
                model_prob = pred["model_probability"]
                db.add(Prediction(
                    game_id=game.id,
                    model_version=model_version,
                    market=pred["market"],
                    selection=pred["selection"],
                    model_probability=model_prob,
                ))
        await db.commit()
    print(f"[{datetime.utcnow().isoformat()}] Models ran for {len(games)} games (version={model_version})")


async def job_pull_results():
    from app.pipeline.results import record_results_for_date
    today = date.today()
    async with async_session() as db:
        count = await record_results_for_date(today, db)
    print(f"[{datetime.utcnow().isoformat()}] Pulled results for {today}: {count} predictions resolved")


async def job_retrain_models():
    from app.pipeline.retrain import retrain_models
    from app.pipeline.notion_logger import log_training_run
    print(f"[{datetime.utcnow().isoformat()}] Retraining models...")
    async with async_session() as db:
        metrics = await retrain_models(db)
    status = metrics.get("status", "unknown")
    if status == "success":
        notion_ok = await log_training_run(metrics)
        print(f"[{datetime.utcnow().isoformat()}] Retrain complete: version={metrics['version']}, samples={metrics['samples']}, improvement='{metrics['improvement']}', notion={notion_ok}")
        if metrics.get("improvement") and metrics["improvement"].startswith("-"):
            try:
                drop_pct = float(metrics["improvement"].lstrip("-").rstrip("%"))
                if drop_pct > 2.0:
                    print(f"[{datetime.utcnow().isoformat()}] Accuracy dropped {drop_pct:.1f}% > 2% threshold. Triggering tests...")
                    asyncio.ensure_future(job_run_tests())
            except (ValueError, IndexError):
                pass
    else:
        print(f"[{datetime.utcnow().isoformat()}] Retrain skipped: {metrics.get('reason', status)}")


async def job_run_tests():
    print(f"[{datetime.utcnow().isoformat()}] Running conditional tests via TestSprite...")
    if not TESTSPRITE_API_KEY:
        print(f"[{datetime.utcnow().isoformat()}] No TESTSPRITE_API_KEY set. Skipping tests.")
        return
    if not os.path.exists(TESTSPRITE_NODE):
        print(f"[{datetime.utcnow().isoformat()}] TestSprite node module not found at {TESTSPRITE_NODE}. Skipping tests.")
        return
    try:
        proc = await asyncio.create_subprocess_exec(
            "node", TESTSPRITE_NODE, "generateCodeAndExecute",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "API_KEY": TESTSPRITE_API_KEY},
            cwd=str(Path(__file__).resolve().parent.parent.parent),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        out = stdout.decode(errors="replace").strip()
        err = stderr.decode(errors="replace").strip()
        if proc.returncode == 0:
            print(f"[{datetime.utcnow().isoformat()}] Tests completed. Output: {out[:200]}")
        else:
            print(f"[{datetime.utcnow().isoformat()}] Tests failed (code={proc.returncode}): {err[:300]}")
    except asyncio.TimeoutError:
        print(f"[{datetime.utcnow().isoformat()}] Tests timed out after 300s.")
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Tests error: {e}")


def setup_scheduler():
    scheduler.add_job(job_pull_lineups, "cron", hour=6, minute=0, id="pull_lineups")
    scheduler.add_job(job_pull_odds, "cron", hour=7, minute=0, id="pull_odds")
    scheduler.add_job(job_run_models, "cron", hour=8, minute=0, id="run_models")
    scheduler.add_job(job_pull_results, "cron", hour=22, minute=0, id="pull_results")
    scheduler.add_job(job_retrain_models, "cron", hour=22, minute=30, id="retrain_models")
    scheduler.start()
