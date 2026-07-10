"""Estado de polling por provider (idempotência)."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProviderState(Base):
    __tablename__ = "provider_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    match_external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_event_external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_poll_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
