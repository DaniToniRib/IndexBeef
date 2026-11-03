from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin

if TYPE_CHECKING:
    from app.models.avaliacao import Avaliacao


class CaixaVirtualAvaliacao(SyncMixin, Base):
    """Caixa virtual calculada pelo pipeline (docs/06)."""

    __tablename__ = "caixa_virtual_avaliacao"
    __table_args__ = (
        UniqueConstraint("avaliacao_id", name="uq_caixa_virtual_avaliacao_avaliacao"),
    )

    avaliacao_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("avaliacao.id", ondelete="CASCADE"), nullable=False,
    )

    c_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    p_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    l_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    volume_cm3: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    volume_l: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    ipl: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    compacidade: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    indice_comprimento: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)

    avaliacao: Mapped[Avaliacao] = relationship(back_populates="caixa_virtual")
