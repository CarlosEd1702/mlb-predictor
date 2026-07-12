from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def calibration_curve(db: AsyncSession) -> list[dict]:
    rows = await db.execute(
        text("""
            SELECT
                width_bucket(p.model_probability, 0, 1, 10) AS bucket,
                MIN(p.model_probability) AS bin_min,
                MAX(p.model_probability) AS bin_max,
                COUNT(*) AS total,
                SUM(CASE WHEN r.won = true THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN r.won = false THEN 1 ELSE 0 END) AS losses
            FROM predictions p
            JOIN results r ON r.prediction_id = p.id
            WHERE p.market = 'h2h'
            GROUP BY bucket
            ORDER BY bucket
        """)
    )
    bins = []
    for row in rows:
        bucket, bin_min, bin_max, total, wins, losses = row
        win_rate = wins / total if total > 0 else 0
        mid_prob = (bin_min + bin_max) / 2
        bins.append({
            "bucket": bucket,
            "bin_min": round(float(bin_min), 3),
            "bin_max": round(float(bin_max), 3),
            "bin_mid": round(mid_prob, 3),
            "total": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 4),
            "error": round(win_rate - mid_prob, 4),
        })
    return bins


async def error_breakdown(db: AsyncSession) -> dict:
    by_market = await db.execute(
        text("""
            SELECT
                p.market,
                COUNT(*) AS total,
                SUM(CASE WHEN r.won = true THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN r.won = false THEN 1 ELSE 0 END) AS losses,
                AVG(p.model_probability) AS avg_prob,
                AVG(p.edge) AS avg_edge
            FROM predictions p
            JOIN results r ON r.prediction_id = p.id
            GROUP BY p.market
            ORDER BY total DESC
        """)
    )
    markets = []
    for row in by_market:
        market, total, wins, losses, avg_prob, avg_edge = row
        win_rate = wins / total if total > 0 else 0
        markets.append({
            "market": market,
            "total": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 4),
            "avg_prob": round(float(avg_prob), 4) if avg_prob else 0,
            "avg_edge": round(float(avg_edge), 4) if avg_edge else 0,
        })

    by_team = await db.execute(
        text("""
            SELECT
                CASE WHEN p.selection LIKE '% win' THEN
                    SUBSTRING(p.selection, 1, LENGTH(p.selection) - 4)
                ELSE p.selection END AS team,
                COUNT(*) AS total,
                SUM(CASE WHEN r.won = true THEN 1 ELSE 0 END) AS wins
            FROM predictions p
            JOIN results r ON r.prediction_id = p.id
            WHERE p.market = 'h2h'
            GROUP BY team
            ORDER BY total DESC
        """)
    )
    teams = []
    for row in by_team:
        team, total, wins = row
        teams.append({
            "team": team,
            "total": total,
            "wins": wins,
            "win_rate": round(wins / total, 4) if total > 0 else 0,
        })

    return {
        "by_market": markets,
        "by_team": teams,
    }
