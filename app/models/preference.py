"""Preferências de notificação do usuário (config campeonatos/jogadores)."""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Sport


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    sport: Mapped[Sport] = mapped_column(default=Sport.FOOTBALL, nullable=False)
    competition_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitions.id"), nullable=True
    )
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    notify_p1: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_p2: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_p3: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    language: Mapped[str] = mapped_column(String(8), default="pt-BR", nullable=False)

    user: Mapped["User"] = relationship(back_populates="preferences")
