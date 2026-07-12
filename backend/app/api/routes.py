import os
import pickle
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import Game, Prediction, Result, ModelVersion
from app.models.features import build_game_features, build_feature_matrix
from app.models.trainer import ModelTrainer
from app.pipeline.odds_api import fetch_upcoming_events, extract_odds
from app.pipeline.calibration import calibration_curve, error_breakdown
from app.pipeline.news import fetch_game_context, fetch_schedule_weather, fetch_recent_transactions, fetch_team_streaks
from app.pipeline.monitor import get_last_retrain, get_last_results_pull, get_daily_accuracy, get_pending_picks, get_scheduler_status

_TEAM_PARK: dict[str, str] = {
    "ARI": "Chase Field",
    "ATL": "Truist Park",
    "BAL": "Oriole Park at Camden Yards",
    "BOS": "Fenway Park",
    "CHC": "Wrigley Field",
    "CWS": "Guaranteed Rate Field",
    "CIN": "Great American Ball Park",
    "CLE": "Progressive Field",
    "COL": "Coors Field",
    "DET": "Comerica Park",
    "HOU": "Minute Maid Park",
    "KC": "Kauffman Stadium",
    "LAA": "Angel Stadium",
    "LAD": "Dodger Stadium",
    "MIA": "LoanDepot Park",
    "MIL": "American Family Field",
    "MIN": "Target Field",
    "NYM": "Citi Field",
    "NYY": "Yankee Stadium",
    "OAK": "Oakland Coliseum",
    "PHI": "Citizens Bank Park",
    "PIT": "PNC Park",
    "SD": "Petco Park",
    "SF": "Oracle Park",
    "SEA": "T-Mobile Park",
    "STL": "Busch Stadium",
    "TB": "Tropicana Field",
    "TEX": "Globe Life Field",
    "TOR": "Rogers Centre",
    "WSN": "Nationals Park",
}

_TEAM_ABBR: dict[str, str] = {
    "Arizona Diamondbacks": "ARI",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSN",
    "Athletics": "OAK",
}


def _team_abbr(name: str) -> str:
    return _TEAM_ABBR.get(name, name)

router = APIRouter()

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "trainer.pkl")
_trainer_cache: ModelTrainer | None = None


def _load_trainer() -> ModelTrainer | None:
    global _trainer_cache
    if _trainer_cache is not None:
        return _trainer_cache
    _trainer_cache = ModelTrainer.load()
    if not _trainer_cache.models:
        _trainer_cache = None
    return _trainer_cache


async def _team_records(db: AsyncSession) -> dict[str, dict]:
    rows = await db.execute(
        text("""
            SELECT team, SUM(games) as games, SUM(wins) as wins FROM (
                SELECT home_team as team, COUNT(*) as games, SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) as wins
                FROM games WHERE status = 'final' GROUP BY home_team
                UNION ALL
                SELECT away_team as team, COUNT(*) as games, SUM(CASE WHEN away_score > home_score THEN 1 ELSE 0 END) as wins
                FROM games WHERE status = 'final' GROUP BY away_team
            ) t GROUP BY team
        """)
    )
    records = {}
    for row in rows:
        team, g, w = row
        records[team] = {"wins": w, "losses": g - w, "games": g}
    return records


_team_stats_cache: dict[str, dict] | None = None


async def _team_stats(db: AsyncSession) -> dict[str, dict]:
    global _team_stats_cache
    if _team_stats_cache is not None:
        return _team_stats_cache

    rows = await db.execute(
        text("""
            SELECT team,
                AVG(k9_rolling) as k9,
                AVG(era_rolling_15) as era,
                AVG(bb9_rolling) as bb9
            FROM pitchers_game_log GROUP BY team
        """)
    )
    pitcher_stats: dict[str, dict] = {}
    for row in rows:
        pitcher_stats[row[0]] = {
            "k9": row[1] if row[1] else 9.0,
            "era": row[2] if row[2] else 4.0,
            "bb9": row[3] if row[3] else 3.0,
        }

    rows = await db.execute(
        text("""
            SELECT team, AVG(woba_rolling_15) as woba
            FROM batters_game_log GROUP BY team
        """)
    )
    batter_stats: dict[str, float] = {}
    for row in rows:
        batter_stats[row[0]] = row[1] if row[1] else 0.300

    _team_stats_cache = {}
    all_teams = set(pitcher_stats.keys()) | set(batter_stats.keys())
    for team in all_teams:
        ps = pitcher_stats.get(team, {})
        _team_stats_cache[team] = {
            "k9": ps.get("k9", 9.0),
            "era": ps.get("era", 4.0),
            "bb9": ps.get("bb9", 3.0),
            "woba": batter_stats.get(team, 0.300),
        }
    return _team_stats_cache


def _american_odds_to_implied(price: int) -> float:
    if price > 0:
        return 100 / (price + 100)
    else:
        return abs(price) / (abs(price) + 100)


@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/proximos")
async def proximos_partidos(db: AsyncSession = Depends(get_db)):
    events = await fetch_upcoming_events()
    if not events:
        return {"games": []}

    records = await _team_records(db)
    team_stats = await _team_stats(db)
    trainer = _load_trainer()

    weather_by_game: dict[str, dict] = {}
    injuries = await fetch_recent_transactions(7)
    streaks = await fetch_team_streaks()

    games_list = []
    for ev in events:
        home_team = _team_abbr(ev.get("home_team", ""))
        away_team = _team_abbr(ev.get("away_team", ""))
        home_full = ev.get("home_team", "")
        away_full = ev.get("away_team", "")
        commence = ev.get("commence_time", "")
        odds_id = ev.get("id", "")
        game_date = commence[:10] if commence else str(date.today())
        game_date_obj = date.fromisoformat(game_date)

        if game_date_obj not in weather_by_game:
            weather_by_game[game_date_obj] = await fetch_schedule_weather(game_date_obj)

        game = await db.execute(
            select(Game).where(
                Game.home_team == home_team,
                Game.away_team == away_team,
                Game.game_date == game_date_obj,
            )
        )
        db_game = game.scalar_one_or_none()
        if not db_game:
            db_game = Game(
                game_date=game_date_obj,
                home_team=home_team,
                away_team=away_team,
                park=_TEAM_PARK.get(home_team),
                status="scheduled",
            )
            db.add(db_game)
            await db.flush()

        pred_data = None
        odds_data = extract_odds(ev)

        if trainer:
            try:
                features = await build_game_features(db_game.id, db)
                if features:
                    hs = team_stats.get(home_team, {})
                    as_ = team_stats.get(away_team, {})

                    if features.get("home_pitcher_k9", 0) == 0:
                        features["home_pitcher_k9"] = hs.get("k9", 9.0)
                        features["home_pitcher_era"] = hs.get("era", 4.0)
                        features["home_pitcher_bb9"] = hs.get("bb9", 3.0)
                    if features.get("away_pitcher_k9", 0) == 0:
                        features["away_pitcher_k9"] = as_.get("k9", 9.0)
                        features["away_pitcher_era"] = as_.get("era", 4.0)
                        features["away_pitcher_bb9"] = as_.get("bb9", 3.0)
                    if features.get("home_lineup_woba", 0.300) == 0.300:
                        features["home_lineup_woba"] = hs.get("woba", 0.300)
                        features["away_lineup_woba"] = as_.get("woba", 0.300)

                    w_key = f"{away_team}_@{home_team}"
                    game_w = weather_by_game.get(game_date_obj, {}).get(w_key, {}).get("weather", {})
                    if game_w.get("temperature") is not None:
                        features["temperature"] = float(game_w["temperature"])
                    if game_w.get("wind"):
                        wind_val = game_w["wind"].split()[0]
                        try:
                            features["wind_speed"] = float(wind_val)
                        except ValueError:
                            pass

                    matrix = build_feature_matrix([features])

                    home_prob = 0.5
                    predicted_runs = 8.0
                    if "moneyline" in trainer.models:
                        home_prob = float(trainer.predict_proba(matrix, "moneyline")[0])
                    if "total_runs" in trainer.models:
                        predicted_runs = float(trainer.predict(matrix, "total_runs")[0])

                    h2h = odds_data.get("h2h", {})
                    home_price = h2h.get(home_full)
                    away_price = h2h.get(away_full)

                    prob_h = round(home_prob, 4)
                    prob_a = round(1 - home_prob, 4)
                    pred_data = {
                        "home_win_prob": prob_h,
                        "away_win_prob": prob_a,
                        "favorite": home_full if home_prob > 0.5 else away_full,
                        "favorite_prob": round(max(home_prob, 1 - home_prob), 4),
                        "predicted_total_runs": round(predicted_runs, 1),
                    }

                    if home_price:
                        market_prob_h = _american_odds_to_implied(home_price)
                        vig_free = market_prob_h / (market_prob_h + _american_odds_to_implied(away_price))
                        edge_h = round(prob_h - vig_free, 4)
                        pred_data["edge_home"] = edge_h
                        edge_a = round(prob_a - (1 - vig_free), 4)
                        pred_data["edge_away"] = edge_a

                        fav_edge = edge_h if home_prob > 0.5 else edge_a
                        fav_selection = f"{home_full} win" if home_prob > 0.5 else f"{away_full} win"
                        confidence = "high" if fav_edge > 0.05 else ("medium" if fav_edge > 0.02 else "low")

                        existing = await db.execute(
                            select(Prediction).where(
                                Prediction.game_id == db_game.id,
                                Prediction.market == "h2h",
                            )
                        )
                        if not existing.scalar_one_or_none():
                            db.add(Prediction(
                                game_id=db_game.id,
                                model_version="v0.1",
                                market="h2h",
                                selection=fav_selection,
                                model_probability=max(prob_h, prob_a),
                                market_probability=round(vig_free if home_prob > 0.5 else (1 - vig_free), 4),
                                edge=fav_edge,
                                confidence=confidence,
                            ))

                        if "total_runs" in trainer.models:
                            existing = await db.execute(
                                select(Prediction).where(
                                    Prediction.game_id == db_game.id,
                                    Prediction.market == "totals",
                                )
                            )
                            if not existing.scalar_one_or_none():
                                db.add(Prediction(
                                    game_id=db_game.id,
                                    model_version="v0.1",
                                    market="totals",
                                    selection=f"Over {round(predicted_runs)}.5",
                                    model_probability=round(predicted_runs / 12, 4),
                                    edge=None,
                                    confidence=None,
                                ))
            except Exception as e:
                print(f"Prediction error for game {db_game.id}: {e}")

        home_rec = records.get(home_team, {})
        away_rec = records.get(away_team, {})
        home_record = f"{home_rec.get('wins', 0)}-{home_rec.get('losses', 0)}"
        away_record = f"{away_rec.get('wins', 0)}-{away_rec.get('losses', 0)}"

        w_key = f"{away_team}_@{home_team}"
        game_w = weather_by_game.get(game_date_obj, {}).get(w_key, {}).get("weather", {})

        games_list.append({
            "id": odds_id,
            "game_id": db_game.id,
            "commence_time": commence,
            "home_team": home_full,
            "away_team": away_full,
            "home_abbr": home_team,
            "away_abbr": away_team,
            "home_record": home_record,
            "away_record": away_record,
            "home_streak": streaks.get(home_team, ""),
            "away_streak": streaks.get(away_team, ""),
            "weather": game_w,
            "home_injuries": injuries.get(home_team, []),
            "away_injuries": injuries.get(away_team, []),
            "odds": odds_data,
            "prediction": pred_data,
        })

    await db.commit()
    return {"games": games_list}


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


@router.get("/partidos")
async def partidos_por_fecha(
    fecha: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    game_date = date.fromisoformat(fecha) if fecha else date.today()
    stmt = select(Game).where(Game.game_date == game_date).order_by(Game.home_team)
    result = await db.execute(stmt)
    games = result.scalars().all()
    return {
        "date": game_date.isoformat(),
        "games": [
            {
                "id": g.id,
                "home_team": g.home_team,
                "away_team": g.away_team,
                "game_date": g.game_date.isoformat(),
                "status": g.status,
                "home_score": g.home_score,
                "away_score": g.away_score,
            }
            for g in games
        ],
    }


@router.get("/partido/{game_id}")
async def detalle_partido(game_id: int, db: AsyncSession = Depends(get_db)):
    game = await db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail={"error": "Partido no encontrado"})

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


@router.get("/resultados")
async def resultados_por_fecha(
    fecha: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    game_date = date.fromisoformat(fecha) if fecha else date.today()
    stmt = (
        select(Game, Prediction, Result)
        .join(Prediction, Prediction.game_id == Game.id)
        .join(Result, Result.prediction_id == Prediction.id)
        .where(Game.game_date == game_date)
        .order_by(Game.home_team)
    )
    rows = await db.execute(stmt)
    items = []
    for game, pred, result in rows:
        items.append({
            "game_id": game.id,
            "home_team": game.home_team,
            "away_team": game.away_team,
            "home_score": game.home_score,
            "away_score": game.away_score,
            "status": game.status,
            "prediction": {
                "id": pred.id,
                "market": pred.market,
                "selection": pred.selection,
                "model_probability": pred.model_probability,
                "edge": pred.edge,
            },
            "result": {
                "won": result.won,
                "actual_value": result.actual_value,
                "clv": result.clv,
            },
        })
    return {"date": game_date.isoformat(), "results": items}


@router.get("/analytics/calibration")
async def calibration(db: AsyncSession = Depends(get_db)):
    bins = await calibration_curve(db)
    total = sum(b["total"] for b in bins)
    mse = sum(b["error"] ** 2 * b["total"] for b in bins) / total if total > 0 else 0
    return {
        "bins": bins,
        "mse": round(mse, 6),
        "total_picks": total,
    }


@router.get("/analytics/errors")
async def errors(db: AsyncSession = Depends(get_db)):
    data = await error_breakdown(db)
    return data


@router.get("/contexto")
async def game_context(
    home_team: str = Query(...),
    away_team: str = Query(...),
    fecha: Optional[str] = Query(None),
):
    game_date = date.fromisoformat(fecha) if fecha else date.today()
    ctx = await fetch_game_context(home_team, away_team, game_date)
    return ctx


@router.get("/noticias")
async def noticias():
    injuries = await fetch_recent_transactions(7)
    streaks = await fetch_team_streaks()
    return {
        "injuries": injuries,
        "streaks": streaks,
    }


@router.get("/monitor")
async def monitor(db: AsyncSession = Depends(get_db)):
    last_retrain = await get_last_retrain(db)
    last_results = await get_last_results_pull(db)
    daily_accuracy = await get_daily_accuracy(db, 14)
    pending_picks = await get_pending_picks(db)
    scheduler_jobs = get_scheduler_status()
    return {
        "last_retrain": last_retrain,
        "last_results_pull": last_results,
        "daily_accuracy": daily_accuracy,
        "pending_picks": pending_picks,
        "scheduler_jobs": scheduler_jobs,
    }


@router.get("/modelos")
async def listar_modelos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ModelVersion).order_by(ModelVersion.training_date.desc())
    )
    versions = result.scalars().all()
    return {
        "versions": [
            {
                "id": v.id,
                "version_label": v.version_label,
                "market": v.market,
                "training_date": v.training_date.isoformat(),
                "training_samples": v.training_samples,
                "metrics": v.metrics,
                "feature_importance": v.feature_importance,
                "parent_version": v.parent_version,
                "is_active": v.is_active,
            }
            for v in versions
        ]
    }


@router.get("/modelos/actual")
async def modelo_actual(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.is_active == True)
    )
    versions = result.scalars().all()
    grouped: dict[str, list] = {}
    for v in versions:
        grouped.setdefault(v.version_label, []).append({
            "market": v.market,
            "metrics": v.metrics,
            "training_date": v.training_date.isoformat(),
            "training_samples": v.training_samples,
        })
    return {
        "versions": grouped,
    }


@router.post("/modelos/rollback/{version_id}")
async def rollback_modelo(version_id: int, db: AsyncSession = Depends(get_db)):
    target = await db.get(ModelVersion, version_id)
    if not target:
        raise HTTPException(status_code=404, detail={"status": "error", "reason": "version not found"})

    version_pkl = f"trainer_{target.version_label}.pkl"
    vpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", version_pkl)
    if not os.path.exists(vpath):
        raise HTTPException(status_code=404, detail={"status": "error", "reason": f"model file {version_pkl} not found"})

    result = await db.execute(
        select(ModelVersion).where(ModelVersion.is_active == True)
    )
    for old in result.scalars().all():
        old.is_active = False

    result = await db.execute(
        select(ModelVersion).where(
            ModelVersion.version_label == target.version_label,
            ModelVersion.market == target.market,
        )
    )
    for v in result.scalars().all():
        v.is_active = True

    await db.commit()

    global _trainer_cache
    _trainer_cache = ModelTrainer.load(version_pkl)
    _trainer_cache.save()

    return {"status": "ok", "version": target.version_label, "market": target.market}
