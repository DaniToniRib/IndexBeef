from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, ForeignKey, Numeric, SmallInteger, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin

if TYPE_CHECKING:
    from app.models.animal import Animal


class DadosGeneticos(SyncMixin, Base):
    """DEPs por animal — uma linha por animal (upsert por animal_id)."""

    __tablename__ = "dados_geneticos"
    __table_args__ = (UniqueConstraint("animal_id", name="uq_dados_geneticos_animal"),)

    animal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False,
    )

    # Programa de avaliacao genetica (PMGZ, ANCP, Geneplus, etc.)
    programa: Mapped[str | None] = mapped_column(String, nullable=True)
    safra: Mapped[str | None] = mapped_column(String, nullable=True)

    # DEPs como dict — ex: {"P120": 1.2, "P210": 3.4, "P450": 5.6, "PE": 0.8}
    deps: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    indice_programa: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    deca: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    data_importacao: Mapped[date | None] = mapped_column(Date, nullable=True)

    animal: Mapped[Animal] = relationship(back_populates="dados_geneticos")
