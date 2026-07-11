import numpy as np


def american_to_implied_prob(american_price: int) -> float:
    if american_price > 0:
        return 100 / (american_price + 100)
    else:
        return abs(american_price) / (abs(american_price) + 100)


def remove_vig(market_probs: dict[str, float]) -> dict[str, float]:
    total = sum(market_probs.values())
    if total == 0:
        return market_probs
    return {k: v / total for k, v in market_probs.items()}


def calculate_edge(
    model_prob: float,
    market_american_price: int,
) -> dict:
    market_prob = american_to_implied_prob(market_american_price)
    fair_market_prob = market_prob

    edge = model_prob - fair_market_prob
    kelly_fraction = edge / fair_market_prob if fair_market_prob > 0 else 0
    kelly_fraction = max(0, min(kelly_fraction, 0.25))

    confidence = "low"
    if edge > 0.05:
        confidence = "high"
    elif edge > 0.02:
        confidence = "medium"

    return {
        "model_probability": round(model_prob, 4),
        "market_probability": round(market_prob, 4),
        "edge": round(edge, 4),
        "edge_pct": round(edge * 100, 2),
        "kelly_fraction": round(kelly_fraction, 4),
        "confidence": confidence,
    }


def filter_picks(
    picks: list[dict],
    min_edge: float = 0.03,
    min_confidence: str = "low",
) -> list[dict]:
    confidence_levels = {"low": 0, "medium": 1, "high": 2}
    min_level = confidence_levels.get(min_confidence, 0)

    filtered = []
    for pick in picks:
        edge = pick.get("edge", 0)
        confidence = pick.get("confidence", "low")
        if edge >= min_edge and confidence_levels.get(confidence, 0) >= min_level:
            filtered.append(pick)
    return filtered
