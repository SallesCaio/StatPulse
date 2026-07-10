"""Jogadores (Radar/Heat Check)."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Sport


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    sport: Mapped[Sport] = mapped_column(default=Sport.FOOTBALL, nullable=False)
    position: Mapped[str | None] = mapped_column(String(16), nullable=True)

    team: Mapped["Team | None"] = relationship(back_populates="players")
