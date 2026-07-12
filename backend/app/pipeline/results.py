from datetime import date, datetime
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Game, Prediction, Result


async def _american_to_implied(price: int) -> float:
    if price > 0:
        return 100 / (price + 100)
    return abs(price) / (abs(price) + 100)


async def fetch_game_results(game_date: date) -> list[dict]:
    url = f"{settings.statcast_base_url}/api/v1/schedule"
    params = {"date": game_date.isoformat(), "sport_id": "1"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for date_group in data.get("dates", []):
        for g in date_group.get("games", []):
            status = g.get("status", {}).get("detailedState", "")
            if status != "Final":
                continue
            teams = g["teams"]
            home = teams["home"]["team"]["abbreviation"]
            away = teams["away"]["team"]["abbreviation"]
            home_score = teams["home"].get("score", 0)
            away_score = teams["away"].get("score", 0)
            results.append({
                "home_team": home,
                "away_team": away,
                "home_score": home_score,
                "away_score": away_score,
                "game_date": game_date,
                "status": "final",
            })
    return results


async def record_results_for_date(game_date: date, db: AsyncSession) -> int:
    results = await fetch_game_results(game_date)
    count = 0

    for r in results:
        game = await db.execute(
            select(Game).where(
                Game.home_team == r["home_team"],
                Game.away_team == r["away_team"],
                Game.game_date == r["game_date"],
            )
        )
        db_game = game.scalar_one_or_none()
        if not db_game:
            continue

        db_game.home_score = r["home_score"]
        db_game.away_score = r["away_score"]
        db_game.status = "final"

        predictions = await db.execute(
            select(Prediction).where(Prediction.game_id == db_game.id)
        )
        for pred in predictions.scalars().all():
            won = None
            actual = None
            if pred.market == "h2h":
                home_won = r["home_score"] > r["away_score"]
                if pred.selection.endswith(" win"):
                    team_name = pred.selection[:-4]
                    team = _resolve_team(team_name, r["home_team"], r["away_team"])
                    won = (team == r["home_team"] and home_won) or (team == r["away_team"] and not home_won)
                actual = float(r["home_score"] - r["away_score"])
            elif pred.market == "totals":
                total = r["home_score"] + r["away_score"]
                if "Over" in pred.selection:
                    try:
                        line = float(pred.selection.replace("Over ", "").replace("Under ", ""))
                        won = total > line
                    except ValueError:
                        won = None
                actual = float(total)
            elif pred.market == "spreads":
                pass

            existing_result = await db.execute(
                select(Result).where(Result.prediction_id == pred.id)
            )
            if existing_result.scalar_one_or_none():
                continue

            clv = None
            closing = await db.execute(
                select(Game).where(
                    Game.home_team == r["home_team"],
                    Game.away_team == r["away_team"],
                    Game.game_date == r["game_date"],
                )
            )
            closing_game = closing.scalar_one_or_none()

            if won is not None:
                db.add(Result(
                    prediction_id=pred.id,
                    actual_value=actual,
                    won=won,
                    clv=clv,
                    recorded_at=datetime.utcnow(),
                ))
                count += 1

    await db.commit()
    return count


def _resolve_team(name: str, home_team: str, away_team: str) -> str:
    from app.api.routes import _TEAM_ABBR
    reverse = {v: k for k, v in _TEAM_ABBR.items()}
    if name in _TEAM_ABBR:
        return _TEAM_ABBR[name]
    if name in reverse:
        return reverse[name]
    return name
