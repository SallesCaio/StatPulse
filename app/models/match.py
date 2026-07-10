"""Partidas."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import MatchStatus, Sport


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    sport: Mapped[Sport] = mapped_column(default=Sport.FOOTBALL, nullable=False)
    competition_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitions.id"), nullable=True
    )
    home_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    away_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    status: Mapped[MatchStatus] = mapped_column(
        default=MatchStatus.SCHEDULED, nullable=False, index=True
    )
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score_home: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_away: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    competition: Mapped["Competition | None"] = relationship(back_populates="matches")
    events: Mapped[list["Event"]] = relationship(back_populates="match")
