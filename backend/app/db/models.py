from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    home_team: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    away_team: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    park: Mapped[str] = mapped_column(String(50), nullable=True)
    home_pitcher_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    away_pitcher_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PitcherGameLog(Base):
    __tablename__ = "pitchers_game_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pitcher_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    pitcher_name: Mapped[str] = mapped_column(String(100), nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    team: Mapped[str] = mapped_column(String(10), nullable=False)
    opponent: Mapped[str] = mapped_column(String(10), nullable=False)
    game_date: Mapped[date] = mapped_column(Date, nullable=False)
    ip: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    k: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    er: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pitches: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_velocity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    era_rolling_15: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    era_rolling_30: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fip_rolling_15: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    k9_rolling: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bb9_rolling: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    game: Mapped["Game"] = relationship(backref="pitcher_logs")


class BatterGameLog(Base):
    __tablename__ = "batters_game_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batter_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    batter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    team: Mapped[str] = mapped_column(String(10), nullable=False)
    opponent: Mapped[str] = mapped_column(String(10), nullable=False)
    game_date: Mapped[date] = mapped_column(Date, nullable=False)
    ab: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    h: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rbi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    k: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_rolling_15: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    woba_rolling_15: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exit_velocity_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    barrel_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    game: Mapped["Game"] = relationship(backref="batter_logs")


class Lineup(Base):
    __tablename__ = "lineups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False, index=True)
    team: Mapped[str] = mapped_column(String(10), nullable=False)
    batting_order: Mapped[int] = mapped_column(Integer, nullable=False)
    player_id: Mapped[str] = mapped_column(String(20), nullable=False)
    player_name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str] = mapped_column(String(5), nullable=True)

    game: Mapped["Game"] = relationship(backref="lineups")


class ParkFactor(Base):
    __tablename__ = "park_factors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    park: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    hr_factor: Mapped[float] = mapped_column(Float, nullable=False)
    runs_factor: Mapped[float] = mapped_column(Float, nullable=False)
    single_factor: Mapped[float] = mapped_column(Float, nullable=False)
    double_factor: Mapped[float] = mapped_column(Float, nullable=False)
    triple_factor: Mapped[float] = mapped_column(Float, nullable=False)


class Weather(Base):
    __tablename__ = "weather"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False, index=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_direction: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    conditions: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    game: Mapped["Game"] = relationship(backref="weather")


class OddsHistory(Base):
    __tablename__ = "odds_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False, index=True)
    sportsbook: Mapped[str] = mapped_column(String(50), nullable=False)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    selection: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    implied_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    is_closing: Mapped[bool] = mapped_column(Boolean, default=False)

    game: Mapped["Game"] = relationship(backref="odds")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    selection: Mapped[str] = mapped_column(String(100), nullable=False)
    model_probability: Mapped[float] = mapped_column(Float, nullable=False)
    market_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    edge: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    simulated_median: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    game: Mapped["Game"] = relationship(backref="predictions")


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), nullable=False, index=True)
    actual_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    won: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    closing_line_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    closing_line_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    clv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prediction: Mapped["Prediction"] = relationship(backref="result")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_label: Mapped[str] = mapped_column(String(20), nullable=False)
    market: Mapped[str] = mapped_column(String(20), nullable=False)
    training_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    training_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    feature_importance: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    parent_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("version_label", "market", name="uq_version_market"),
    )
