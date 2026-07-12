from datetime import date, datetime, timedelta
from typing import Optional

import httpx

from app.config import settings

_TEAM_IDS: dict[str, int] = {
    "ARI": 109, "ATL": 144, "BAL": 110, "BOS": 111,
    "CHC": 112, "CWS": 145, "CIN": 113, "CLE": 114,
    "COL": 115, "DET": 116, "HOU": 117, "KC": 118,
    "LAA": 108, "LAD": 119, "MIA": 146, "MIL": 158,
    "MIN": 142, "NYM": 121, "NYY": 147, "OAK": 133,
    "PHI": 143, "PIT": 134, "SD": 135, "SF": 137,
    "SEA": 136, "STL": 138, "TB": 139, "TEX": 140,
    "TOR": 141, "WSN": 120,
}

_team_id_cache: dict[str, int] | None = None


async def fetch_schedule_weather(game_date: date) -> dict[str, dict]:
    """Fetch schedule with weather for a given date, keyed by team abbreviation."""
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.get(
            "https://statsapi.mlb.com/api/v1/schedule",
            params={"sportId": 1, "date": game_date.isoformat(), "hydrate": "weather"},
        )
        r.raise_for_status()
        data = r.json()

    team_rev: dict[int, str] = {v: k for k, v in _TEAM_IDS.items()}
    games: dict[str, dict] = {}
    for d in data.get("dates", []):
        for g in d.get("games", []):
            teams = g["teams"]
            away_id = teams["away"]["team"]["id"]
            home_id = teams["home"]["team"]["id"]
            away_abbr = team_rev.get(away_id, "")
            home_abbr = team_rev.get(home_id, "")
            if not away_abbr or not home_abbr:
                continue
            w = g.get("weather", {})
            games[f"{away_abbr}_@{home_abbr}"] = {
                "weather": {
                    "condition": w.get("condition", ""),
                    "temperature": w.get("temp"),
                    "wind": w.get("wind", ""),
                },
                "venue": g.get("venue", {}).get("name", ""),
                "game_date": g.get("gameDate", ""),
            }
    return games


async def fetch_recent_transactions(days: int = 7) -> dict[str, list[dict]]:
    """Fetch recent transactions/injuries grouped by team abbreviation."""
    end = date.today()
    start = end - timedelta(days=days)
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.get(
            "https://statsapi.mlb.com/api/v1/transactions",
            params={
                "sportId": 1,
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
            },
        )
        r.raise_for_status()
        data = r.json()

    by_team: dict[str, list[dict]] = {}
    team_rev: dict[int, str] = {v: k for k, v in _TEAM_IDS.items()}

    for t in data.get("transactions", []):
        for team_info in t.get("teams", []):
            mlb_id = team_info.get("id")
            abbr = team_rev.get(mlb_id)
            if not abbr:
                continue
            desc = t.get("description", "")
            is_injury = any(kw in desc.lower() for kw in ["injured", "placed", "activated", "rehab"])
            if not is_injury:
                continue
            if abbr not in by_team:
                by_team[abbr] = []
            if len(by_team[abbr]) < 5:
                by_team[abbr].append({
                    "type": t.get("type", ""),
                    "description": desc,
                    "date": t.get("date", "")[:10],
                })

    return by_team


async def fetch_team_streaks() -> dict[str, str]:
    """Fetch current win/loss streaks for all teams."""
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.get(
            "https://statsapi.mlb.com/api/v1/standings",
            params={"leagueId": 103, "season": date.today().year, "standingsTypes": "regularSeason"},
        )
        r.raise_for_status()
        data = r.json()

    streaks: dict[str, str] = {}
    team_rev: dict[int, str] = {v: k for k, v in _TEAM_IDS.items()}
    for rec in data.get("records", []):
        for team_rec in rec.get("teamRecords", []):
            mlb_id = team_rec["team"]["id"]
            abbr = team_rev.get(mlb_id)
            if abbr:
                streak = team_rec.get("streak", {})
                code = streak.get("streakCode", "")
                streaks[abbr] = code
    return streaks


async def fetch_game_context(
    home_team: str,
    away_team: str,
    game_date: date,
) -> dict:
    """Fetch all context for a specific game: weather, injuries, streaks."""
    weather = await fetch_schedule_weather(game_date)
    injuries = await fetch_recent_transactions(7)
    streaks = await fetch_team_streaks()

    game_key = f"{away_team}_@{home_team}"
    w = weather.get(game_key, {}).get("weather", {})
    temp = w.get("temperature")
    if temp is not None:
        try:
            temp = float(temp)
        except (ValueError, TypeError):
            temp = None

    return {
        "weather": {
            "condition": w.get("condition", ""),
            "temperature": temp,
            "wind": w.get("wind", ""),
        },
        "home_injuries": injuries.get(home_team, []),
        "away_injuries": injuries.get(away_team, []),
        "home_streak": streaks.get(home_team, ""),
        "away_streak": streaks.get(away_team, ""),
    }
