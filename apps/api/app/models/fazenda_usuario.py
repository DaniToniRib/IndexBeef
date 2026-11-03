from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class FazendaUsuario(SyncMixin, Base):
    """Associação entre usuário e fazenda com papel (admin, tecnico, operador)."""

    __tablename__ = "fazenda_usuario"
    __table_args__ = (UniqueConstraint("fazenda_id", "usuario_id"),)

    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False,
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False,
    )
    papel: Mapped[str] = mapped_column(String, nullable=False)  # admin/tecnico/operador

    usuario: Mapped[Usuario] = relationship(back_populates="fazendas")
