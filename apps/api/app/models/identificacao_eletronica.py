from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import ModoRfid

if TYPE_CHECKING:
    from app.models.animal import Animal


class IdentificacaoEletronica(SyncMixin, Base):
    """Botton RFID / brinco eletronico (ISO 11784/11785). Ver docs/11 §1.

    Separado de `Animal` porque o animal pode trocar de brinco ao longo da
    vida (perda, falha do chip, re-identificacao). O EID de 15 digitos
    comeca com 076 (BR) + 12 digitos do fabricante/serial.
    """

    __tablename__ = "identificacao_eletronica"

    animal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False,
    )
    eid: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    vid: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    modo: Mapped[ModoRfid] = mapped_column(
        SAEnum(ModoRfid, name="modo_rfid"), nullable=False, default=ModoRfid.FDX_B,
    )
    fabricante: Mapped[str | None] = mapped_column(String, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ativo_desde: Mapped[date] = mapped_column(Date, nullable=False)
    inativo_desde: Mapped[date | None] = mapped_column(Date, nullable=True)
    motivo_troca: Mapped[str | None] = mapped_column(Text, nullable=True)

    animal: Mapped[Animal] = relationship(back_populates="identificacoes_eletronicas")
