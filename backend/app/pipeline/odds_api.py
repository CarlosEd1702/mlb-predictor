import httpx
from datetime import date

from app.config import settings


def _american_to_implied_prob(american_price: int) -> float:
    if american_price > 0:
        return 100 / (american_price + 100)
    else:
        return abs(american_price) / (abs(american_price) + 100)


def extract_odds(event: dict) -> dict:
    odds = {"h2h": {}, "spreads": {}, "totals": {}}
    for bm in event.get("bookmakers", []):
        for market in bm.get("markets", []):
            key = market["key"]
            if key not in odds:
                continue
            for outcome in market.get("outcomes", []):
                name = outcome.get("name", outcome.get("description", ""))
                price = outcome["price"]
                point = outcome.get("point", None)
                if key == "h2h":
                    odds["h2h"][name] = price
                elif key == "spreads":
                    odds["spreads"][name] = {"price": price, "point": point}
                elif key == "totals":
                    odds["totals"][name] = {"price": price, "point": point}
    return odds


async def fetch_upcoming_events(region: str = "us") -> list[dict]:
    if not settings.odds_api_key:
        return []

    url = f"{settings.odds_api_base_url}/sports/baseball_mlb/odds"
    params = {
        "apiKey": settings.odds_api_key,
        "regions": region,
        "markets": "h2h,spreads,totals",
        "oddsFormat": "american",
        "dateFormat": "iso",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def fetch_odds_for_date(game_date: date, region: str = "us") -> list[dict]:
    if not settings.odds_api_key:
        return []

    url = f"{settings.odds_api_base_url}/sports/baseball_mlb/odds"
    params = {
        "apiKey": settings.odds_api_key,
        "regions": region,
        "markets": "h2h,spreads,totals,player_strikeouts",
        "oddsFormat": "american",
        "dateFormat": "iso",
        "commenceTimeFrom": f"{game_date.isoformat()}T00:00:00Z",
        "commenceTimeTo": f"{game_date.isoformat()}T23:59:59Z",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    odds_records = []
    for event in data:
        game_id = event.get("id")
        for bookmaker in event.get("bookmakers", []):
            sportsbook = bookmaker["key"]
            for market in bookmaker.get("markets", []):
                market_key = market["key"]
                for outcome in market.get("outcomes", []):
                    price = outcome["price"]
                    odds_records.append({
                        "game_id": game_id,
                        "sportsbook": sportsbook,
                        "market": market_key,
                        "selection": outcome.get("name", outcome.get("description", "")),
                        "price": price,
                        "implied_prob": _american_to_implied_prob(price),
                        "timestamp": bookmaker.get("last_update", ""),
                    })
    return odds_records
