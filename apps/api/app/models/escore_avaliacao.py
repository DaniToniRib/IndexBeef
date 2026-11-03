from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, SmallInteger, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin

if TYPE_CHECKING:
    from app.models.avaliacao import Avaliacao


class EscoreAvaliacao(SyncMixin, Base):
    """ECC + EPMURAS por avaliacao (uma linha por avaliacao)."""

    __tablename__ = "escore_avaliacao"
    __table_args__ = (UniqueConstraint("avaliacao_id", name="uq_escore_avaliacao_avaliacao"),)

    avaliacao_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("avaliacao.id", ondelete="CASCADE"), nullable=False,
    )

    frame_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)

    # ECC sugerido pelo sistema e confirmado pelo tecnico
    ecc_sugerido: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)
    ecc_final: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)

    # EPMURAS — cada letra: sugerido (sistema) e final (tecnico)
    # E = Estrutura
    e_sugerido: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    e_final: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    # P = Precocidade
    p_sugerido: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    p_final: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    # M = Musculosidade
    m_sugerido: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    m_final: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    # U = Umbigo
    u_sugerido: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    u_final: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    # R = Racial
    r_sugerido: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    r_final: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    # A = Aprumos
    a_sugerido: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    a_final: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    # S = Sexualidade
    s_sugerido: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    s_final: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    avaliacao: Mapped[Avaliacao] = relationship(back_populates="escore")
