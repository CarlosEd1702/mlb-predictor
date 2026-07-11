from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import Game, Prediction, Result

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/predicciones/hoy")
async def predicciones_hoy(db: AsyncSession = Depends(get_db)):
    today = date.today()
    stmt = (
        select(Prediction, Game)
        .join(Game, Prediction.game_id == Game.id)
        .where(Game.game_date == today)
        .where(Game.status == "scheduled")
        .order_by(Prediction.edge.desc().nullslast())
    )
    result = await db.execute(stmt)
    rows = result.all()
    picks = []
    for pred, game in rows:
        picks.append({
            "prediction_id": pred.id,
            "game_id": game.id,
            "home_team": game.home_team,
            "away_team": game.away_team,
            "game_date": game.game_date.isoformat(),
            "market": pred.market,
            "selection": pred.selection,
            "model_probability": pred.model_probability,
            "market_probability": pred.market_probability,
            "edge": pred.edge,
            "confidence": pred.confidence,
        })
    return {"date": today.isoformat(), "picks": picks}


@router.get("/partido/{game_id}")
async def detalle_partido(game_id: int, db: AsyncSession = Depends(get_db)):
    game = await db.get(Game, game_id)
    if not game:
        return {"error": "Partido no encontrado"}, 404

    stmt = select(Prediction).where(Prediction.game_id == game_id)
    result = await db.execute(stmt)
    predictions = result.scalars().all()

    return {
        "game": {
            "id": game.id,
            "date": game.game_date.isoformat(),
            "home_team": game.home_team,
            "away_team": game.away_team,
            "park": game.park,
            "home_score": game.home_score,
            "away_score": game.away_score,
            "status": game.status,
        },
        "predictions": [
            {
                "id": p.id,
                "market": p.market,
                "selection": p.selection,
                "model_probability": p.model_probability,
                "edge": p.edge,
            }
            for p in predictions
        ],
    }


@router.get("/historial")
async def historial(
    prop_type: Optional[str] = Query(None, alias="tipo"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Prediction, Result).join(Result, Prediction.id == Result.prediction_id)
    if prop_type:
        stmt = stmt.where(Prediction.market == prop_type)

    result = await db.execute(stmt)
    rows = result.all()
    total = len(rows)
    wins = sum(1 for _, r in rows if r.won)
    losses = sum(1 for _, r in rows if r.won is False)
    pushes = sum(1 for _, r in rows if r.won is None)

    return {
        "total_picks": total,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "accuracy": round(wins / total, 4) if total > 0 else 0,
    }


@router.get("/historial/{prop_type}")
async def historial_por_tipo(prop_type: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Prediction, Result)
        .join(Result, Prediction.id == Result.prediction_id)
        .where(Prediction.market == prop_type)
    )
    result = await db.execute(stmt)
    rows = result.all()
    total = len(rows)
    wins = sum(1 for _, r in rows if r.won)
    losses = sum(1 for _, r in rows if r.won is False)

    return {
        "prop_type": prop_type,
        "total_picks": total,
        "wins": wins,
        "losses": losses,
        "accuracy": round(wins / total, 4) if total > 0 else 0,
    }
