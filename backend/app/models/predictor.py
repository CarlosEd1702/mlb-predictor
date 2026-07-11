import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.features import build_game_features, build_feature_matrix
from app.models.trainer import ModelTrainer
from app.simulation.monte_carlo import simulate_game


async def predict_game(
    game_id: int,
    trainer: ModelTrainer,
    db: AsyncSession,
) -> dict:
    features = await build_game_features(game_id, db)
    matrix = build_feature_matrix([features])

    predictions = []
    if "moneyline" in trainer.models:
        home_win_prob = float(trainer.predict_proba(matrix, "moneyline")[0])
        predictions.append({
            "market": "h2h",
            "selection": f"{features['home_team']} win",
            "model_probability": home_win_prob,
        })

    if "total_runs" in trainer.models:
        predicted_runs = float(trainer.predict(matrix, "total_runs")[0])
        over_prob = _prob_over(predicted_runs, matrix)
        predictions.append({
            "market": "totals",
            "selection": f"Over {round(predicted_runs)}.5",
            "model_probability": over_prob,
        })

    sim_result = await _run_simulation(game_id, features, db)

    return {
        "game_id": game_id,
        "features": features,
        "predictions": predictions,
        "simulation": sim_result,
    }


async def _run_simulation(
    game_id: int, features: dict, db: AsyncSession
) -> dict:
    n_sims = 10000
    home_runs, away_runs = [], []
    for _ in range(n_sims):
        hr, ar = simulate_game(features)
        home_runs.append(hr)
        away_runs.append(ar)

    home_runs = np.array(home_runs)
    away_runs = np.array(away_runs)
    total_runs = home_runs + away_runs

    home_win_sim = np.mean(home_runs > away_runs)
    avg_total = float(np.mean(total_runs))
    median_total = float(np.median(total_runs))

    return {
        "n_simulations": n_sims,
        "home_win_prob_sim": float(home_win_sim),
        "avg_total_runs": avg_total,
        "median_total_runs": median_total,
        "home_runs_p10": float(np.percentile(home_runs, 10)),
        "home_runs_p90": float(np.percentile(home_runs, 90)),
        "away_runs_p10": float(np.percentile(away_runs, 10)),
        "away_runs_p90": float(np.percentile(away_runs, 90)),
    }


def _prob_over(predicted_runs: float, features: np.ndarray) -> float:
    return 0.5
