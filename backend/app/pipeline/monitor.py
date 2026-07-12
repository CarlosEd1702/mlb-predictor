from datetime import date, datetime, timedelta

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ModelVersion, Prediction, Result, Game
from app.pipeline.scheduler import scheduler


async def get_last_retrain(db: AsyncSession) -> dict | None:
    result = await db.execute(
        select(ModelVersion)
        .where(ModelVersion.market == "moneyline")
        .order_by(ModelVersion.training_date.desc())
        .limit(1)
    )
    v = result.scalar_one_or_none()
    if not v:
        return None
    return {
        "version_label": v.version_label,
        "training_date": v.training_date.isoformat(),
        "accuracy": v.metrics.get("accuracy") if v.metrics else None,
        "samples": v.training_samples,
    }


async def get_last_results_pull(db: AsyncSession) -> str | None:
    result = await db.execute(
        select(func.max(Game.updated_at))
        .where(Game.status == "final")
    )
    val = result.scalar()
    return val.isoformat() if val else None


async def get_daily_accuracy(db: AsyncSession, days: int = 14) -> list[dict]:
    since = date.today() - timedelta(days=days)
    rows = await db.execute(
        text("""
            SELECT
                g.game_date,
                COUNT(*) AS total,
                SUM(CASE WHEN r.won = true THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN r.won = false THEN 1 ELSE 0 END) AS losses
            FROM results r
            JOIN predictions p ON p.id = r.prediction_id
            JOIN games g ON g.id = p.game_id
            WHERE g.game_date >= :since
            GROUP BY g.game_date
            ORDER BY g.game_date
        """),
        {"since": since},
    )
    items = []
    for row in rows:
        total = row.total
        wins = row.wins or 0
        items.append({
            "date": row.game_date.isoformat(),
            "total_picks": total,
            "wins": wins,
            "losses": row.losses or 0,
            "accuracy": round(wins / total, 4) if total > 0 else 0,
        })
    return items


async def get_pending_picks(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count(Prediction.id))
        .join(Game, Prediction.game_id == Game.id)
        .where(Game.status == "scheduled")
    )
    return result.scalar() or 0


async def get_scheduler_status() -> list[dict]:
    jobs = scheduler.get_jobs()
    return [
        {
            "id": j.id,
            "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
        }
        for j in jobs
    ]
