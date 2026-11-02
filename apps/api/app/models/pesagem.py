from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import OrigemPesagem

if TYPE_CHECKING:
    from app.models.animal import Animal
    from app.models.avaliacao import Avaliacao


class Pesagem(SyncMixin, Base):
    __tablename__ = "pesagem"

    animal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False,
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    peso_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    origem: Mapped[OrigemPesagem] = mapped_column(
        SAEnum(OrigemPesagem, name="origem_pesagem"), nullable=False,
    )
    avaliacao_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("avaliacao.id", ondelete="SET NULL"), nullable=True,
    )

    animal: Mapped[Animal] = relationship(back_populates="pesagens")
    avaliacao: Mapped[Avaliacao | None] = relationship(back_populates="pesagens")
