from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import TipoCaptura, VistaCaptura

if TYPE_CHECKING:
    from app.models.avaliacao import Avaliacao


class Captura(SyncMixin, Base):
    __tablename__ = "captura"

    avaliacao_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("avaliacao.id", ondelete="CASCADE"), nullable=False,
    )
    tipo: Mapped[TipoCaptura] = mapped_column(
        SAEnum(TipoCaptura, name="tipo_captura"), nullable=False,
    )
    vista: Mapped[VistaCaptura] = mapped_column(
        SAEnum(VistaCaptura, name="vista_captura"), nullable=False,
    )
    arquivo_url: Mapped[str] = mapped_column(String, nullable=False)
    dispositivo: Mapped[str | None] = mapped_column(String, nullable=True)
    px_por_cm: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    erro_calibracao_px: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)

    avaliacao: Mapped[Avaliacao] = relationship(back_populates="capturas")
