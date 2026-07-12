import os

from app.config import settings


async def log_training_run(metrics: dict) -> bool:
    db_id = settings.notion_model_db_id
    token = settings.notion_token
    if not db_id or not token:
        return False

    try:
        from notion_client import AsyncClient

        client = AsyncClient(auth=token)

        version = metrics.get("version", "unknown")
        improvement = metrics.get("improvement", "")
        money = metrics.get("moneyline", {})
        total = metrics.get("total_runs", {})

        properties = {
            "Name": {"title": [{"text": {"content": f"{version} — moneyline"}}]},
            "Date": {"date": {"start": os.environ.get("TRAINING_DATE", "") or "2026-07-11"}},
            "Market": {"select": {"name": "moneyline"}},
            "Version": {"rich_text": [{"text": {"content": version}}]},
            "Samples": {"number": metrics.get("samples", 0)},
            "Active": {"checkbox": True},
        }

        if money.get("accuracy") is not None:
            properties["Accuracy"] = {"number": round(money["accuracy"] * 100, 2)}
        if money.get("log_loss") is not None:
            properties["Log Loss"] = {"number": round(money["log_loss"], 4)}
        if money.get("brier_score") is not None:
            properties["Brier Score"] = {"number": round(money["brier_score"], 4)}
        if money.get("calibration_error") is not None:
            properties["Calibration Error"] = {"number": round(money["calibration_error"], 4)}
        if total.get("rmse") is not None:
            properties["RMSE"] = {"number": round(total["rmse"], 4)}
        if total.get("mae") is not None:
            properties["MAE"] = {"number": round(total["mae"], 4)}
        if improvement:
            properties["Improvement"] = {"rich_text": [{"text": {"content": improvement[:200]}}]}

        await client.pages.create(
            parent={"database_id": db_id},
            properties=properties,
        )

        if total:
            properties2 = dict(properties)
            properties2["Name"] = {"title": [{"text": {"content": f"{version} — total_runs"}}]}
            properties2["Market"] = {"select": {"name": "total_runs"}}
            await client.pages.create(
                parent={"database_id": db_id},
                properties=properties2,
            )

        return True
    except Exception as e:
        print(f"[notion_logger] Failed to log training run: {e}")
        return False
