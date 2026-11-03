from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import StatusCampanha, TipoAplicacaoSanitaria

if TYPE_CHECKING:
    from app.models.aplicacao_sanitaria import AplicacaoSanitaria
    from app.models.fazenda import Fazenda


class Campanha(SyncMixin, Base):
    """Campanha de rebanho (vacinacao em massa, vermifugacao de lote etc).

    Agrupa varias `AplicacaoSanitaria` com o mesmo protocolo (ver docs/11 §4).
    """

    __tablename__ = "campanha"

    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False,
    )
    nome: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[TipoAplicacaoSanitaria] = mapped_column(
        SAEnum(TipoAplicacaoSanitaria, name="tipo_aplicacao_sanitaria"),
        nullable=False,
    )
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    protocolo: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[StatusCampanha] = mapped_column(
        SAEnum(StatusCampanha, name="status_campanha"),
        nullable=False,
        default=StatusCampanha.planejada,
    )

    fazenda: Mapped[Fazenda] = relationship()
    aplicacoes: Mapped[list[AplicacaoSanitaria]] = relationship(
        back_populates="campanha",
    )
