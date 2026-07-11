import random
from dataclasses import dataclass

import numpy as np


@dataclass
class SimulationInput:
    home_pitcher_k9: float = 9.0
    home_pitcher_bb9: float = 3.0
    home_pitcher_era: float = 4.0
    away_pitcher_k9: float = 9.0
    away_pitcher_bb9: float = 3.0
    away_pitcher_era: float = 4.0
    home_lineup_woba: float = 0.320
    away_lineup_woba: float = 0.320
    park_runs_factor: float = 1.0
    temperature: float = 70.0
    wind_speed: float = 0.0


def _inning_runs(
    pitcher_k9: float,
    pitcher_bb9: float,
    lineup_woba: float,
    park_factor: float,
) -> float:
    base_runs = 0.5
    k_adjustment = max(0.2, 1.0 - (pitcher_k9 - 8.0) * 0.05)
    bb_adjustment = 1.0 + (pitcher_bb9 - 3.0) * 0.03
    woba_adjustment = (lineup_woba - 0.320) * 10
    park_adj = (park_factor - 1.0) * 0.5 + 1.0
    expected = base_runs * k_adjustment * bb_adjustment * (1 + woba_adjustment) * park_adj
    return max(0, expected)


def _sample_inning_runs(expected: float) -> int:
    if expected <= 0:
        return 0
    p_zero = np.exp(-expected)
    r = random.random()
    if r < p_zero:
        return 0
    runs = 1
    cumulative = p_zero
    while r > cumulative and runs < 20:
        p = (expected ** runs) * np.exp(-expected) / _factorial(runs)
        cumulative += p
        runs += 1
    return runs - 1


def _factorial(n: int) -> int:
    return 1 if n <= 1 else n * _factorial(n - 1)


def simulate_game(features: dict) -> tuple[int, int]:
    inp = SimulationInput(
        home_pitcher_k9=features.get("home_pitcher_k9", 9.0),
        home_pitcher_bb9=features.get("home_pitcher_bb9", 3.0),
        home_pitcher_era=features.get("home_pitcher_era", 4.0),
        away_pitcher_k9=features.get("away_pitcher_k9", 9.0),
        away_pitcher_bb9=features.get("away_pitcher_bb9", 3.0),
        away_pitcher_era=features.get("away_pitcher_era", 4.0),
        home_lineup_woba=features.get("home_lineup_woba", 0.320),
        away_lineup_woba=features.get("away_lineup_woba", 0.320),
        park_runs_factor=features.get("park_runs_factor", 1.0),
        temperature=features.get("temperature", 70.0),
        wind_speed=features.get("wind_speed", 0.0),
    )

    home_runs = 0
    away_runs = 0

    for inning in range(1, 10):
        exp_away = _inning_runs(
            inp.home_pitcher_k9, inp.home_pitcher_bb9,
            inp.away_lineup_woba, inp.park_runs_factor,
        )
        away_runs += _sample_inning_runs(exp_away)

        exp_home = _inning_runs(
            inp.away_pitcher_k9, inp.away_pitcher_bb9,
            inp.home_lineup_woba, inp.park_runs_factor,
        )
        home_runs += _sample_inning_runs(exp_home)

    if home_runs == away_runs:
        extra_innings = random.randint(1, 3)
        for _ in range(extra_innings):
            away_runs += _sample_inning_runs(exp_away * 0.7)
            home_runs += _sample_inning_runs(exp_home * 0.7)

    return home_runs, away_runs


def simulate_game_batch(
    features: dict, n_simulations: int = 10000
) -> tuple[np.ndarray, np.ndarray]:
    home_runs_list = []
    away_runs_list = []
    for _ in range(n_simulations):
        hr, ar = simulate_game(features)
        home_runs_list.append(hr)
        away_runs_list.append(ar)
    return np.array(home_runs_list), np.array(away_runs_list)
