from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import TipoEventoGeofence

if TYPE_CHECKING:
    from app.models.animal import Animal
    from app.models.geofence import Geofence


class EventoGeofence(SyncMixin, Base):
    """Entrada ou saida de um animal numa geofence (ver docs/11 §3)."""

    __tablename__ = "evento_geofence"

    animal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False,
    )
    geofence_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("geofence.id", ondelete="CASCADE"), nullable=False,
    )
    tipo: Mapped[TipoEventoGeofence] = mapped_column(
        SAEnum(TipoEventoGeofence, name="tipo_evento_geofence"), nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    animal: Mapped[Animal] = relationship()
    geofence: Mapped[Geofence] = relationship(back_populates="eventos")
