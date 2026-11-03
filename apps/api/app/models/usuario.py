from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin

if TYPE_CHECKING:
    from app.models.fazenda_usuario import FazendaUsuario


class Usuario(SyncMixin, Base):
    """Usuário do sistema (criador, técnico, operador)."""

    __tablename__ = "usuario"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    fazendas: Mapped[list[FazendaUsuario]] = relationship(back_populates="usuario")
