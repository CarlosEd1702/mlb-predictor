import pandas as pd
import httpx
from datetime import date, timedelta

from app.config import settings


async def fetch_statcast_data(start_date: date, end_date: date) -> pd.DataFrame:
    url = f"{settings.statcast_base_url}/statcast_search/csv"
    params = {
        "all": "true",
        "hfPT": "",
        "hfAB": "",
        "hfBBT": "",
        "hfPR": "",
        "hfZ": "",
        "stadium": "",
        "hfBBL": "",
        "hfNewZones": "",
        "hfGT": "R|PO|S|D|T|HR|E|H|B",
        "hfSea": "",
        "hfSit": "",
        "player_type": "batter",
        "hfOuts": "",
        "opponent": "",
        "pitcher_throws": "",
        "batter_stands": "",
        "hfSA": "",
        "game_date_gt": start_date.isoformat(),
        "game_date_lt": end_date.isoformat(),
        "team": "",
        "position": "",
        "hfInfield": "",
        "hfRF": "",
        "group_by": "name",
        "min_pitches": "0",
        "min_results": "0",
        "min_pas": "0",
        "sort_col": "pitches",
        "sort_order": "desc",
        "min_abs": "0",
        "type": "details",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

    import io
    df = pd.read_csv(io.StringIO(response.text))
    return df


async def fetch_pitch_arsenal(pitcher_id: str) -> dict:
    url = f"{settings.statcast_base_url}/pitcher/{pitcher_id}?type=stats&section=arsenal"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
    return response.json()


async def get_daily_games(game_date: date) -> list[dict]:
    url = f"{settings.statcast_base_url}/api/v1/schedule"
    params = {"date": game_date.isoformat(), "sport_id": "1"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    games = []
    for date_group in data.get("dates", []):
        for game_data in date_group.get("games", []):
            games.append({
                "game_id": game_data["gamePk"],
                "home_team": game_data["teams"]["home"]["team"]["abbreviation"],
                "away_team": game_data["teams"]["away"]["team"]["abbreviation"],
                "game_date": game_date.isoformat(),
                "status": game_data.get("status", {}).get("detailedState", "scheduled"),
            })
    return games
