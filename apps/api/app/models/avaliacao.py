from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import StatusAvaliacao

if TYPE_CHECKING:
    from app.models.animal import Animal
    from app.models.captura import Captura
    from app.models.pesagem import Pesagem


class Avaliacao(SyncMixin, Base):
    __tablename__ = "avaliacao"

    animal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False,
    )
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # FK para a tabela usuario ainda nao existe (prompt futuro); fica como UUID solto.
    avaliador_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    status: Mapped[StatusAvaliacao] = mapped_column(
        SAEnum(StatusAvaliacao, name="status_avaliacao"),
        nullable=False,
        default=StatusAvaliacao.capturada,
    )
    versao_pipeline: Mapped[str | None] = mapped_column(String, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # resultado: payload JSON produzido pelo pipeline (ver indexbeef_vision.pipeline).
    # Guardado como coluna JSONB enquanto nao migramos para as tabelas estruturadas
    # (medidas, caixa_virtual, escores, predicao) descritas no docs/06.
    resultado: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    animal: Mapped[Animal] = relationship(back_populates="avaliacoes")
    capturas: Mapped[list[Captura]] = relationship(
        back_populates="avaliacao", cascade="all, delete-orphan",
    )
    pesagens: Mapped[list[Pesagem]] = relationship(back_populates="avaliacao")
