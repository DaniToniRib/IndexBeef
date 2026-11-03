from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin

if TYPE_CHECKING:
    from app.models.avaliacao import Avaliacao


class MedidaAvaliacao(SyncMixin, Base):
    """Uma linha por avaliacao com todas as medidas lineares e angulos (docs/06)."""

    __tablename__ = "medida_avaliacao"
    __table_args__ = (UniqueConstraint("avaliacao_id", name="uq_medida_avaliacao_avaliacao"),)

    avaliacao_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("avaliacao.id", ondelete="CASCADE"), nullable=False,
    )

    altura_cernelha_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    altura_cernelha_conf: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    altura_garupa_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    altura_garupa_conf: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    comprimento_corporal_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    comprimento_corporal_conf: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    profundidade_toracica_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    profundidade_toracica_conf: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    comprimento_garupa_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    comprimento_garupa_conf: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    largura_garupa_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    largura_garupa_conf: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    altura_cupim_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    altura_cupim_conf: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    umbigo_chao_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    umbigo_chao_conf: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    perimetro_toracico_est_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True,
    )
    perimetro_toracico_est_conf: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    inclinacao_garupa_graus: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    jarrete_graus: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    # Medicoes manuais de referencia (hipometro/fita/paquimetro — subconjunto ~1:3)
    # NAO devem ser sobrescritas pelo worker (ON CONFLICT DO UPDATE nao inclui essas colunas)
    altura_cernelha_manual_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    altura_garupa_manual_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    comprimento_corporal_manual_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True,
    )
    largura_garupa_manual_cm: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    perimetro_toracico_manual_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True,
    )

    avaliacao: Mapped[Avaliacao] = relationship(back_populates="medida")
