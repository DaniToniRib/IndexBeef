from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import CategoriaLote

if TYPE_CHECKING:
    from app.models.animal import Animal
    from app.models.fazenda import Fazenda


class Lote(SyncMixin, Base):
    __tablename__ = "lote"

    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False,
    )
    nome: Mapped[str] = mapped_column(String, nullable=False)
    categoria: Mapped[CategoriaLote] = mapped_column(
        SAEnum(CategoriaLote, name="categoria_lote"), nullable=False,
    )

    fazenda: Mapped[Fazenda] = relationship(back_populates="lotes")
    animais: Mapped[list[Animal]] = relationship(
        back_populates="lote", cascade="all, delete-orphan",
    )
