from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin

if TYPE_CHECKING:
    from app.models.avaliacao import Avaliacao


class PredicaoAvaliacao(SyncMixin, Base):
    """Predicoes calculadas pelo pipeline: peso atual e projecoes de crescimento.

    tipo: "peso_atual" | "peso_18m" | "peso_24m" | "peso_30m"
    """

    __tablename__ = "predicao_avaliacao"

    avaliacao_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("avaliacao.id", ondelete="CASCADE"), nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    valor: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    faixa_min: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    faixa_max: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    confianca: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    metodo: Mapped[str | None] = mapped_column(String, nullable=True)

    avaliacao: Mapped[Avaliacao] = relationship(back_populates="predicoes")
