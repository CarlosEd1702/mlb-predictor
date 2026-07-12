from datetime import datetime

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Game, PitcherGameLog, BatterGameLog, ParkFactor, Weather, ModelVersion
from app.models.trainer import ModelTrainer

FEATURE_KEYS = [
    "home_pitcher_k9", "home_pitcher_era", "home_pitcher_bb9",
    "away_pitcher_k9", "away_pitcher_era", "away_pitcher_bb9",
    "home_lineup_woba", "away_lineup_woba",
    "park_hr_factor", "park_runs_factor",
    "temperature", "wind_speed",
]


async def _load_training_data(db: AsyncSession) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    result = await db.execute(
        select(Game).where(Game.status == "final").order_by(Game.game_date)
    )
    games: list[Game] = result.scalars().all()

    rows = []
    y_money = []
    y_total = []

    pitcher_batch = await db.execute(
        select(PitcherGameLog).where(PitcherGameLog.game_id.in_([g.id for g in games]))
    )
    pitcher_map: dict[int, list[PitcherGameLog]] = {}
    for pl in pitcher_batch.scalars().all():
        pitcher_map.setdefault(pl.game_id, []).append(pl)

    batter_batch = await db.execute(
        select(BatterGameLog).where(BatterGameLog.game_id.in_([g.id for g in games]))
    )
    batter_map: dict[int, list[BatterGameLog]] = {}
    for bl in batter_batch.scalars().all():
        batter_map.setdefault(bl.game_id, []).append(bl)

    park_result = await db.execute(select(ParkFactor).order_by(ParkFactor.year.desc()))
    park_map: dict[str, ParkFactor] = {}
    for pf in park_result.scalars().all():
        if pf.park not in park_map:
            park_map[pf.park] = pf

    weather_batch = await db.execute(
        select(Weather).where(Weather.game_id.in_([g.id for g in games]))
    )
    weather_map: dict[int, Weather] = {w.game_id: w for w in weather_batch.scalars().all()}

    for game in games:
        row = {
            "game_id": game.id,
            "home_team": game.home_team,
            "away_team": game.away_team,
            "park": game.park or "",
            "home_rest": 0,
            "away_rest": 0,
        }

        logs = pitcher_map.get(game.id, [])
        for pl in logs:
            if pl.team == game.home_team:
                row["home_pitcher_k9"] = pl.k9_rolling if pl.k9_rolling else 0
                row["home_pitcher_era"] = pl.era_rolling_15 if pl.era_rolling_15 else 0
                row["home_pitcher_bb9"] = pl.bb9_rolling if pl.bb9_rolling else 0
            else:
                row["away_pitcher_k9"] = pl.k9_rolling if pl.k9_rolling else 0
                row["away_pitcher_era"] = pl.era_rolling_15 if pl.era_rolling_15 else 0
                row["away_pitcher_bb9"] = pl.bb9_rolling if pl.bb9_rolling else 0

        b_logs = batter_map.get(game.id, [])
        home_woba = [b.woba_rolling_15 for b in b_logs if b.team == game.home_team and b.woba_rolling_15]
        away_woba = [b.woba_rolling_15 for b in b_logs if b.team == game.away_team and b.woba_rolling_15]
        row["home_lineup_woba"] = float(np.mean(home_woba)) if home_woba else 0.300
        row["away_lineup_woba"] = float(np.mean(away_woba)) if away_woba else 0.300

        pf = park_map.get(game.park or "")
        row["park_hr_factor"] = pf.hr_factor if pf else 1.0
        row["park_runs_factor"] = pf.runs_factor if pf else 1.0

        w = weather_map.get(game.id)
        row["temperature"] = w.temperature if w and w.temperature else 70.0
        row["wind_speed"] = w.wind_speed if w and w.wind_speed else 0.0

        features_row = [row.get(k, 0) for k in FEATURE_KEYS]
        rows.append(features_row)

        home_win = 1 if (game.home_score or 0) > (game.away_score or 0) else 0
        y_money.append(home_win)
        y_total.append((game.home_score or 0) + (game.away_score or 0))

    return np.array(rows, dtype=np.float32), np.array(y_money, dtype=np.float32), np.array(y_total, dtype=np.float32), FEATURE_KEYS


async def _get_next_version(db: AsyncSession) -> str:
    result = await db.execute(select(ModelVersion.version_label).distinct().order_by(ModelVersion.version_label.desc()).limit(1))
    latest = result.scalar()
    if not latest:
        return "v0.2"
    try:
        parts = latest.lstrip("v").split(".")
        major = int(parts[0]) if parts else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        minor += 1
        return f"v{major}.{minor}"
    except (ValueError, IndexError):
        return "v0.2"


async def _get_active_metrics(db: AsyncSession) -> dict[str, dict]:
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.is_active == True)
    )
    versions = result.scalars().all()
    return {v.market: v.metrics for v in versions}


def _compute_improvement(current: dict, previous: dict | None) -> str:
    if not previous:
        return "first version"
    parts = []
    for key in ("accuracy", "log_loss", "brier_score", "calibration_error", "rmse", "mae"):
        if key in current and key in previous:
            diff = current[key] - previous[key]
            direction = "+" if diff >= 0 else ""
            if key in ("log_loss", "brier_score", "calibration_error", "rmse", "mae"):
                diff = -diff
            parts.append(f"{key}: {direction}{diff:.4f}")
    return ", ".join(parts)


async def retrain_models(db: AsyncSession) -> dict:
    X, y_money, y_total, feature_names = await _load_training_data(db)

    if len(X) < 50:
        return {"status": "skipped", "reason": f"only {len(X)} training samples available"}

    trainer = ModelTrainer()

    money_metrics = trainer.train_moneyline(X, y_money, feature_names=feature_names, model_name="moneyline")
    total_metrics = trainer.train_total_runs(X, y_total, feature_names=feature_names, model_name="total_runs")

    version_label = await _get_next_version(db)
    previous = await _get_active_metrics(db)

    improvement = _compute_improvement(money_metrics, previous.get("moneyline"))

    feat_imp_money = {}
    if feature_names and trainer.get_metrics("moneyline"):
        imp = trainer.models["moneyline"].feature_importances_
        feat_imp_money = dict(zip(feature_names, [float(v) for v in imp]))

    trainer.save(f"trainer_{version_label}.pkl")
    trainer.save()
    await db.commit()

    now = datetime.utcnow()

    for market, metrics in [("moneyline", money_metrics), ("total_runs", total_metrics)]:
        feat_imp = feat_imp_money if market == "moneyline" else {}
        parent = previous.get(market, {}).get("version_label") if previous else None
        mv = ModelVersion(
            version_label=version_label,
            market=market,
            training_date=now,
            training_samples=len(X),
            metrics=metrics,
            feature_importance=feat_imp,
            parent_version=parent,
            is_active=True,
        )
        db.add(mv)

    result = await db.execute(
        select(ModelVersion).where(ModelVersion.is_active == True, ModelVersion.version_label != version_label)
    )
    for old in result.scalars().all():
        old.is_active = False

    await db.commit()

    return {
        "status": "success",
        "version": version_label,
        "samples": len(X),
        "improvement": improvement,
        "moneyline": money_metrics,
        "total_runs": total_metrics,
    }
