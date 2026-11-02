from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin

if TYPE_CHECKING:
    from app.models.lote import Lote


class Fazenda(SyncMixin, Base):
    __tablename__ = "fazenda"

    nome: Mapped[str] = mapped_column(String, nullable=False)
    municipio: Mapped[str | None] = mapped_column(String, nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    bioma: Mapped[str | None] = mapped_column(String, nullable=True)

    lotes: Mapped[list[Lote]] = relationship(
        back_populates="fazenda", cascade="all, delete-orphan",
    )
