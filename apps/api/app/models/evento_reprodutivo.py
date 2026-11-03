from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Numeric, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import TipoEventoReprodutivo

if TYPE_CHECKING:
    from app.models.animal import Animal


class EventoReprodutivo(SyncMixin, Base):
    """Evento reprodutivo: cobertura, IATF, diagnóstico, parto, aborto, desmama."""

    __tablename__ = "evento_reprodutivo"

    animal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False,
    )
    tipo: Mapped[TipoEventoReprodutivo] = mapped_column(
        SAEnum(TipoEventoReprodutivo, name="tipo_evento_reprodutivo"), nullable=False,
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    resultado: Mapped[str | None] = mapped_column(Text, nullable=True)
    dias_gestacao: Mapped[int | None] = mapped_column(Integer, nullable=True)

    touro_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="SET NULL"), nullable=True,
    )
    bezerro_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="SET NULL"), nullable=True,
    )
    peso_desmama_bezerro: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    animal: Mapped[Animal] = relationship(
        foreign_keys=[animal_id], back_populates="eventos_reprodutivos",
    )
