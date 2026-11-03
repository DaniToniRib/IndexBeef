from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin

if TYPE_CHECKING:
    from app.models.animal import Animal
    from app.models.dispositivo import Dispositivo


class LeituraRfid(SyncMixin, Base):
    """Leitura bruta de bastao/antena RFID (ver docs/11 §1).

    `animal_id` e nullable: a leitura chega antes de termos certeza do
    pareamento. O servico de match preenche quando encontra uma
    IdentificacaoEletronica ativa com o mesmo EID.
    """

    __tablename__ = "leitura_rfid"

    dispositivo_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("dispositivo.id", ondelete="SET NULL"), nullable=True,
    )
    animal_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="SET NULL"), nullable=True,
    )
    eid: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    vid: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    session: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    pareado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    dispositivo: Mapped[Dispositivo | None] = relationship()
    animal: Mapped[Animal | None] = relationship()
