import numpy as np
import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Game, PitcherGameLog, BatterGameLog, ParkFactor, Weather


def _compute_rolling(stats: list[float], window: int = 15) -> float:
    if len(stats) == 0:
        return 0.0
    recent = stats[-window:]
    return sum(recent) / len(recent)


async def build_game_features(game_id: int, db: AsyncSession) -> dict:
    game = await db.get(Game, game_id)
    if not game:
        return {}

    features = {
        "game_id": game_id,
        "home_team": game.home_team,
        "away_team": game.away_team,
        "park": game.park or "",
        "home_rest": 0,
        "away_rest": 0,
    }

    result = await db.execute(
        select(PitcherGameLog).where(PitcherGameLog.game_id == game_id)
    )
    pitcher_logs = result.scalars().all()
    for pl in pitcher_logs:
        if pl.team == game.home_team:
            features["home_pitcher_k9"] = pl.k9_rolling if pl.k9_rolling else 0
            features["home_pitcher_era"] = pl.era_rolling_15 if pl.era_rolling_15 else 0
            features["home_pitcher_bb9"] = pl.bb9_rolling if pl.bb9_rolling else 0
        else:
            features["away_pitcher_k9"] = pl.k9_rolling if pl.k9_rolling else 0
            features["away_pitcher_era"] = pl.era_rolling_15 if pl.era_rolling_15 else 0
            features["away_pitcher_bb9"] = pl.bb9_rolling if pl.bb9_rolling else 0

    result = await db.execute(
        select(BatterGameLog).where(BatterGameLog.game_id == game_id)
    )
    batter_logs = result.scalars().all()
    home_woba = [b.woba_rolling_15 for b in batter_logs if b.team == game.home_team and b.woba_rolling_15]
    away_woba = [b.woba_rolling_15 for b in batter_logs if b.team == game.away_team and b.woba_rolling_15]
    features["home_lineup_woba"] = np.mean(home_woba) if home_woba else 0.300
    features["away_lineup_woba"] = np.mean(away_woba) if away_woba else 0.300

    result = await db.execute(
        select(ParkFactor).where(ParkFactor.park == game.park)
        .order_by(ParkFactor.year.desc()).limit(1)
    )
    pf = result.scalar_one_or_none()
    features["park_hr_factor"] = pf.hr_factor if pf else 1.0
    features["park_runs_factor"] = pf.runs_factor if pf else 1.0

    result = await db.execute(
        select(Weather).where(Weather.game_id == game_id)
    )
    w = result.scalar_one_or_none()
    features["temperature"] = w.temperature if w and w.temperature else 70.0
    features["wind_speed"] = w.wind_speed if w and w.wind_speed else 0.0

    return features


def build_feature_matrix(games_features: list[dict]) -> np.ndarray:
    keys = [
        "home_pitcher_k9", "home_pitcher_era", "home_pitcher_bb9",
        "away_pitcher_k9", "away_pitcher_era", "away_pitcher_bb9",
        "home_lineup_woba", "away_lineup_woba",
        "park_hr_factor", "park_runs_factor",
        "temperature", "wind_speed",
    ]
    matrix = []
    for gf in games_features:
        row = [gf.get(k, 0) for k in keys]
        matrix.append(row)
    return np.array(matrix, dtype=np.float32)
