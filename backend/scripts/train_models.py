"""
Entrenamiento de modelos XGBoost con datos históricos de Statcast.
Uso: python scripts/train_models.py
"""
import argparse
import asyncio
import os
import pickle
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

os.environ["PYTHONPATH"] = "."

from app.db.base import Base, async_session, engine
from app.db.models import Game, PitcherGameLog, BatterGameLog
from app.models.features import build_game_features, build_feature_matrix
from app.models.trainer import ModelTrainer


async def fetch_statcast_season(start_date: date, end_date: date) -> pd.DataFrame:
    import httpx
    import io

    url = "https://baseballsavant.mlb.com/statcast_search/csv"
    params = {
        "all": "true",
        "hfGT": "R|PO|S|D|T|HR|E|H|B",
        "game_date_gt": start_date.isoformat(),
        "game_date_lt": end_date.isoformat(),
        "player_type": "batter",
        "group_by": "name",
        "min_pitches": "0",
        "sort_col": "pitches",
        "sort_order": "desc",
        "type": "details",
    }

    print(f"Fetching Statcast data from {start_date} to {end_date}...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
    print(f"  Got {len(df)} rows")
    return df


def compute_rolling_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["player_id", "game_date"])
    df["game_date"] = pd.to_datetime(df["game_date"])

    rolling_windows = [15, 30]
    for w in rolling_windows:
        for col in ["woba", "avg", "slg", "obp", "k_rate", "bb_rate"]:
            if col in df.columns:
                df[f"{col}_rolling_{w}"] = (
                    df.groupby("player_id")[col]
                    .transform(lambda x: x.rolling(w, min_periods=1).mean())
                )

    if "era" in df.columns:
        df["era_rolling_15"] = df.groupby("pitcher_id")["era"].transform(
            lambda x: x.rolling(15, min_periods=1).mean()
        )
    if "k9" in df.columns:
        df["k9_rolling"] = df.groupby("pitcher_id")["k9"].transform(
            lambda x: x.rolling(15, min_periods=1).mean()
        )

    return df


async def seed_sample_games(db: AsyncSession, df: pd.DataFrame):
    game_dates = df["game_date"].unique()[:50]
    for gd in game_dates:
        day_df = df[df["game_date"] == gd]
        teams = day_df["team"].unique()
        if len(teams) >= 2:
            home = teams[0]
            away = teams[1]
            exists = await db.execute(
                select(Game).where(
                    Game.game_date == gd,
                    Game.home_team == home,
                    Game.away_team == away,
                )
            )
            if not exists.scalar_one_or_none():
                db.add(
                    Game(
                        game_date=gd,
                        home_team=home,
                        away_team=away,
                        park=day_df["venue"].iloc[0] if "venue" in day_df.columns else "Unknown",
                        status="final",
                        home_score=int(np.random.randint(0, 12)),
                        away_score=int(np.random.randint(0, 12)),
                    )
                )
    await db.commit()
    print(f"  Seeded sample games")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-06-01")
    parser.add_argument("--end", default="2025-07-01")
    parser.add_argument("--model-dir", default="models")
    parser.add_argument("--fetch", action="store_true", help="Fetch data from Statcast")
    args = parser.parse_args()

    os.makedirs(args.model_dir, exist_ok=True)
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)

    trainer = ModelTrainer()

    async with async_session() as db:
        games_result = await db.execute(
            select(Game).where(
                Game.game_date.between(start, end),
                Game.status == "final",
            )
        )
        games = games_result.scalars().all()
        print(f"Found {len(games)} completed games in database")

        if not games:
            print("No games found. Use --fetch to download data from Statcast.")
            return

        features_list = []
        labels_ml = []
        labels_total = []

        for game in games:
            gf = await build_game_features(game.id, db)
            if not gf:
                continue
            features_list.append(gf)

            if game.home_score is not None and game.away_score is not None:
                home_win = 1 if game.home_score > game.away_score else 0
                labels_ml.append(home_win)
                labels_total.append(game.home_score + game.away_score)

        if len(features_list) < 50:
            print(f"Not enough game data ({len(features_list)} games). Need at least 50.")
            print("Run --fetch to get more data.")
            return

        X = build_feature_matrix(features_list)
        y_ml = np.array(labels_ml, dtype=np.int32)
        y_total = np.array(labels_total, dtype=np.float32)

        print(f"\nTraining with {len(X)} samples, {X.shape[1]} features")
        print(f"  Moneyline classes: {np.bincount(y_ml)}")
        print(f"  Total runs: mean={y_total.mean():.1f}, std={y_total.std():.1f}")

        print("\nTraining Moneyline model (XGBoost)...")
        ml_results = trainer.train_moneyline(X, y_ml)
        print(f"  Accuracy: {ml_results['accuracy']:.3f}")
        print(f"  Log Loss: {ml_results['log_loss']:.4f}")
        print(f"  Brier:    {ml_results['brier_score']:.4f}")

        print("\nTraining Total Runs model (XGBoost)...")
        tr_results = trainer.train_total_runs(X, y_total)
        print(f"  RMSE: {tr_results['rmse']:.3f}")
        print(f"  MAE:  {tr_results['mae']:.3f}")

        model_path = os.path.join(args.model_dir, "trainer.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(trainer, f)
        print(f"\nModels saved to {model_path}")

        test_indices = len(X) - int(len(X) * 0.2)
        X_test = X[test_indices:]
        y_test_ml = y_ml[test_indices:]

        if len(X_test) > 0:
            ml_preds = trainer.predict_proba(X_test)
            ml_preds_class = (ml_preds > 0.5).astype(int)
            test_acc = np.mean(ml_preds_class == y_test_ml)
            print(f"\nBacktest ({len(X_test)} games):")
            print(f"  Accuracy: {test_acc:.3f}")
            top_pct = 0.25
            n_top = max(1, int(len(X_test) * top_pct))
            top_idx = np.argsort(np.abs(ml_preds - 0.5))[::-1][:n_top]
            top_acc = np.mean(ml_preds_class[top_idx] == y_test_ml[top_idx])
            print(f"  Top {top_pct*100:.0f}% confidence: {top_acc:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
