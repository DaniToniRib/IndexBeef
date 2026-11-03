from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import ResultadoAndrologico

if TYPE_CHECKING:
    from app.models.animal import Animal


class ExameAndrologico(SyncMixin, Base):
    """Exame andrológico de touro."""

    __tablename__ = "exame_andrologico"

    animal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False,
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    perimetro_escrotal_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    resultado: Mapped[ResultadoAndrologico | None] = mapped_column(
        SAEnum(ResultadoAndrologico, name="resultado_andrologico"), nullable=True,
    )
    veterinario: Mapped[str | None] = mapped_column(String, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    animal: Mapped[Animal] = relationship(back_populates="exames_andrologicos")
