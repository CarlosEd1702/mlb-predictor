"""
Script para cargar datos históricos de Statcast en PostgreSQL.
Uso: python scripts/seed_data.py --start 2025-03-27 --end 2025-10-01
"""
import argparse
import asyncio
from datetime import date, timedelta

import asyncpg


DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/mlb_predictor"


async def seed_park_factors(pool):
    parks = [
        ("Angel Stadium", 1.02, 1.01, 1.00, 1.00, 1.00),
        ("Busch Stadium", 0.93, 0.96, 0.98, 0.98, 0.98),
        ("Chase Field", 1.08, 1.07, 1.05, 1.03, 1.02),
        ("Citi Field", 0.95, 0.97, 0.98, 0.99, 0.98),
        ("Citizens Bank Park", 1.12, 1.10, 1.06, 1.04, 1.03),
        ("Coors Field", 1.32, 1.28, 1.15, 1.10, 1.08),
        ("Dodger Stadium", 0.98, 0.99, 1.00, 1.00, 1.00),
        ("Fenway Park", 1.05, 1.03, 1.04, 1.02, 1.01),
        ("Globe Life Field", 0.97, 0.98, 0.99, 0.99, 0.99),
        ("Great American Ball Park", 1.14, 1.11, 1.06, 1.04, 1.03),
        ("Guaranteed Rate Field", 1.03, 1.02, 1.01, 1.01, 1.00),
        ("Kauffman Stadium", 0.94, 0.96, 0.97, 0.98, 0.98),
        ("LoanDepot Park", 0.91, 0.94, 0.96, 0.97, 0.97),
        ("Minute Maid Park", 1.05, 1.04, 1.02, 1.02, 1.01),
        ("Nationals Park", 1.03, 1.02, 1.01, 1.01, 1.00),
        ("Oakland Coliseum", 0.97, 0.98, 0.99, 0.99, 0.99),
        ("Oracle Park", 0.93, 0.95, 0.97, 0.98, 0.98),
        ("Oriole Park at Camden Yards", 1.08, 1.06, 1.04, 1.03, 1.02),
        ("Petco Park", 0.92, 0.95, 0.96, 0.97, 0.98),
        ("PNC Park", 0.99, 1.00, 1.00, 1.00, 1.00),
        ("Progressive Field", 1.02, 1.01, 1.01, 1.01, 1.00),
        ("Rogers Centre", 1.05, 1.04, 1.02, 1.02, 1.01),
        ("Target Field", 0.99, 1.00, 1.00, 1.00, 1.00),
        ("T-Mobile Park", 0.93, 0.96, 0.97, 0.98, 0.98),
        ("Tropicana Field", 0.95, 0.97, 0.98, 0.98, 0.98),
        ("Truist Park", 1.04, 1.03, 1.02, 1.01, 1.01),
        ("Wrigley Field", 1.06, 1.05, 1.03, 1.02, 1.01),
        ("Yankee Stadium", 1.10, 1.08, 1.05, 1.03, 1.02),
    ]

    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM park_factors")
        for park, hr, runs, s, d, t in parks:
            await conn.execute(
                """
                INSERT INTO park_factors (park, year, hr_factor, runs_factor, single_factor, double_factor, triple_factor)
                VALUES ($1, 2025, $2, $3, $4, $5, $6)
                """,
                park, hr, runs, s, d, t,
            )
    print(f"Inserted {len(parks)} park factors")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-03-27")
    parser.add_argument("--end", default="2025-10-01")
    args = parser.parse_args()

    pool = await asyncpg.create_pool(
        user="postgres", password="postgres",
        database="mlb_predictor", host="localhost", port=5432,
    )

    print("Seeding park factors...")
    await seed_park_factors(pool)

    print("Done!")
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
