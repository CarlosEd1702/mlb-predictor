"""
Genera datos sintéticos realistas de partidos MLB para entrenar modelos.
Basado en estadísticas típicas de la temporada 2024-2025.
"""
import asyncio
import random
from datetime import date, timedelta

import numpy as np

from app.db.base import async_session
from app.db.models import Game, PitcherGameLog, BatterGameLog, ParkFactor

TEAMS = [
    "ARI", "ATL", "BAL", "BOS", "CHC", "CWS", "CIN", "CLE",
    "COL", "DET", "HOU", "KC", "LAA", "LAD", "MIA", "MIL",
    "MIN", "NYM", "NYY", "OAK", "PHI", "PIT", "SD", "SF",
    "SEA", "STL", "TB", "TEX", "TOR", "WSH",
]

PARK_FACTORS: dict[str, tuple[float, float]] = {
    "Coors Field": (1.32, 1.28),
    "Great American Ball Park": (1.14, 1.11),
    "Citizens Bank Park": (1.12, 1.10),
    "Yankee Stadium": (1.10, 1.08),
    "Chase Field": (1.08, 1.07),
    "Fenway Park": (1.05, 1.03),
    "Truist Park": (1.04, 1.03),
    "Minute Maid Park": (1.05, 1.04),
    "Wrigley Field": (1.06, 1.05),
    "Oriole Park at Camden Yards": (1.08, 1.06),
    "Rogers Centre": (1.05, 1.04),
    "Target Field": (0.99, 1.00),
    "Dodger Stadium": (0.98, 0.99),
    "Busch Stadium": (0.93, 0.96),
    "Oracle Park": (0.93, 0.95),
    "T-Mobile Park": (0.93, 0.96),
    "Petco Park": (0.92, 0.95),
    "Citi Field": (0.95, 0.97),
    "Kauffman Stadium": (0.94, 0.96),
    "Globe Life Field": (0.97, 0.98),
    "LoanDepot Park": (0.91, 0.94),
    "Oakland Coliseum": (0.97, 0.98),
}

PITCHERS = [
    ("p001", 9.5, 2.3, 3.1), ("p002", 10.2, 2.8, 2.9), ("p003", 8.1, 3.5, 4.2),
    ("p004", 7.5, 4.0, 4.8), ("p005", 11.0, 2.0, 2.5), ("p006", 9.0, 3.0, 3.8),
    ("p007", 8.5, 3.2, 4.0), ("p008", 10.8, 1.9, 2.2), ("p009", 7.2, 4.5, 5.0),
    ("p010", 9.8, 2.5, 3.3), ("p011", 8.8, 3.3, 3.9), ("p012", 11.5, 1.8, 2.0),
    ("p013", 7.8, 3.8, 4.5), ("p014", 9.3, 2.7, 3.4), ("p015", 8.3, 3.6, 4.1),
    ("p016", 10.5, 2.1, 2.7), ("p017", 7.0, 4.2, 5.2), ("p018", 9.7, 2.4, 3.2),
    ("p019", 8.6, 3.1, 3.7), ("p020", 11.2, 1.7, 2.1), ("p021", 10.0, 2.2, 2.8),
    ("p022", 7.6, 4.0, 4.6), ("p023", 9.1, 2.9, 3.5), ("p024", 8.0, 3.7, 4.3),
    ("p025", 10.7, 2.0, 2.4), ("p026", 9.4, 2.6, 3.0), ("p027", 8.2, 3.4, 4.0),
    ("p028", 11.1, 1.8, 2.2), ("p029", 7.3, 4.1, 4.9), ("p030", 9.9, 2.3, 2.9),
    ("p031", 8.7, 3.0, 3.6), ("p032", 10.3, 2.0, 2.6), ("p033", 8.4, 3.3, 3.9),
    ("p034", 11.4, 1.6, 2.0), ("p035", 7.9, 3.9, 4.4), ("p036", 9.6, 2.5, 3.1),
    ("p037", 8.1, 3.6, 4.2), ("p038", 10.1, 2.1, 2.7), ("p039", 9.2, 2.8, 3.4),
    ("p040", 11.3, 1.7, 2.1),
]

BATTER_WOBA = [0.280, 0.300, 0.315, 0.330, 0.345, 0.360, 0.375, 0.390, 0.410, 0.430]


def simulate_game_score(home_p_k9, away_p_k9, home_woba, away_woba, park_runs):
    base_runs = 4.5
    home_adj = (home_woba - 0.320) * 20 - (away_p_k9 - 9.0) * 0.1 + (park_runs - 1.0) * 2
    away_adj = (away_woba - 0.320) * 20 - (home_p_k9 - 9.0) * 0.1 + (park_runs - 1.0) * 1.8
    home_exp = max(0, base_runs + home_adj + random.gauss(0, 1.5))
    away_exp = max(0, base_runs + away_adj + random.gauss(0, 1.5))
    return round(home_exp), round(away_exp)


async def seed():
    import logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    async with async_session() as db:
        result = await db.execute(ParkFactor.__table__.select())
        parks = result.fetchall()
        if not parks:
            print("No park factors found. Run seed_data.py first.")
            return

        start_date = date(2024, 4, 1)
        end_date = date(2024, 9, 30)
        current = start_date
        game_count = 0
        id_counter = [1]

        while current <= end_date:
            if current.weekday() >= 5:
                n_games = random.randint(10, 15)
            else:
                n_games = random.randint(6, 10)

            random.shuffle(TEAMS)
            for i in range(0, min(len(TEAMS) - 1, n_games * 2), 2):
                if i + 1 >= len(TEAMS):
                    break
                home = TEAMS[i]
                away = TEAMS[i + 1]
                park_name = random.choice(list(PARK_FACTORS.keys()))
                park_hr, park_runs = PARK_FACTORS[park_name]

                hp = random.choice(PITCHERS)
                ap = random.choice([p for p in PITCHERS if p[0] != hp[0]])
                home_woba = random.choice(BATTER_WOBA)
                away_woba = random.choice(BATTER_WOBA)

                home_score, away_score = simulate_game_score(
                    hp[1], ap[1], home_woba, away_woba, park_runs
                )

                game = Game(
                    game_date=current,
                    home_team=home,
                    away_team=away,
                    park=park_name,
                    home_pitcher_id=hp[0],
                    away_pitcher_id=ap[0],
                    home_score=home_score,
                    away_score=away_score,
                    status="final",
                )
                db.add(game)
                await db.flush()
                game_id = game.id

                for pid, k9, bb, era in [hp, ap]:
                    team = home if pid == hp[0] else away
                    opp = away if pid == hp[0] else home
                    batters_faced = random.randint(20, 35)
                    k_actual = round(k9 * batters_faced / 27)
                    bb_actual = round(bb * batters_faced / 27)
                    ip = round((batters_faced - bb_actual) / 3, 1)
                    er = round(era * ip / 9, 0) if ip > 0 else 0

                    db.add(PitcherGameLog(
                        pitcher_id=pid,
                        pitcher_name=f"Pitcher_{pid}",
                        game_id=game_id,
                        team=team,
                        opponent=opp,
                        game_date=current,
                        ip=ip,
                        k=int(k_actual),
                        bb=int(bb_actual),
                        er=int(er),
                        pitches=random.randint(60, 110),
                        avg_velocity=round(random.uniform(92, 98), 1),
                        era_rolling_15=round(era, 2),
                        era_rolling_30=round(era + random.uniform(-0.3, 0.3), 2),
                        fip_rolling_15=round(era * 0.9 + random.uniform(-0.2, 0.2), 2),
                        k9_rolling=round(k9, 1),
                        bb9_rolling=round(bb, 1),
                    ))

                for j in range(9):
                    team = home if j % 2 == 0 else away
                    opp = away if j % 2 == 0 else home
                    woba = home_woba if j % 2 == 0 else away_woba
                    db.add(BatterGameLog(
                        batter_id=f"b{id_counter[0]:04d}",
                        batter_name=f"Batter_{id_counter[0]:04d}",
                        game_id=game_id,
                        team=team,
                        opponent=opp,
                        game_date=current,
                        ab=random.randint(3, 5),
                        h=random.randint(0, 3),
                        hr=random.randint(0, 1),
                        rbi=random.randint(0, 4),
                        bb=random.randint(0, 1),
                        k=random.randint(0, 2),
                        woba_rolling_15=round(woba, 3),
                        exit_velocity_avg=round(random.uniform(85, 95), 1),
                        barrel_rate=round(random.uniform(2, 15), 1),
                    ))
                    id_counter[0] += 1

                game_count += 1

            current += timedelta(days=1)
            if game_count % 200 == 0:
                print(f"  {game_count} games created ({current})")

        await db.commit()
        print(f"\nCreated {game_count} games with pitcher and batter logs")
        print(f"Period: {start_date} to {end_date}")
        print(f"Batters created: {id_counter[0] - 1}")


if __name__ == "__main__":
    asyncio.run(seed())
