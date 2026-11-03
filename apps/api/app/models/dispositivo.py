from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, ForeignKey, String, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import StatusDispositivo, TipoDispositivo

if TYPE_CHECKING:
    from app.models.fazenda import Fazenda
    from app.models.pesagem import Pesagem


class Dispositivo(SyncMixin, Base):
    """Equipamento fisico instalado na fazenda (ver docs/11 §2, §3)."""

    __tablename__ = "dispositivo"

    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False,
    )
    tipo: Mapped[TipoDispositivo] = mapped_column(
        SAEnum(TipoDispositivo, name="tipo_dispositivo"), nullable=False,
    )
    modelo: Mapped[str | None] = mapped_column(String, nullable=True)
    fabricante: Mapped[str | None] = mapped_column(String, nullable=True)
    numero_serie: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    data_instalacao: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[StatusDispositivo] = mapped_column(
        SAEnum(StatusDispositivo, name="status_dispositivo"),
        nullable=False,
        default=StatusDispositivo.ativo,
    )
    # Config livre: endpoint, credenciais, cadence, etc. Pode conter segredos
    # — nao expor em listagens publicas.
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    fazenda: Mapped[Fazenda] = relationship(back_populates="dispositivos")
    pesagens: Mapped[list[Pesagem]] = relationship(back_populates="dispositivo")
