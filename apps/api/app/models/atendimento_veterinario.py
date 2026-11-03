from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin

if TYPE_CHECKING:
    from app.models.animal import Animal


class AtendimentoVeterinario(SyncMixin, Base):
    """Atendimento clinico-veterinario registrado (Res. CFMV 1138/2016).

    `veterinario_crmv` e obrigatorio (ver docs/11 §5). Prescricoes ficam em
    `prescricoes_jsonb` como lista — cada item com principio_ativo, dose,
    via, duracao, carencia. Prescricoes "aplicadas de verdade" viram
    AplicacaoSanitaria linkada.
    """

    __tablename__ = "atendimento_veterinario"

    animal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False,
    )
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    veterinario_nome: Mapped[str] = mapped_column(String, nullable=False)
    veterinario_crmv: Mapped[str] = mapped_column(String, nullable=False)  # ex: "SP-12345"
    motivo: Mapped[str] = mapped_column(String, nullable=False)

    queixa: Mapped[str | None] = mapped_column(Text, nullable=True)
    peso_estimado_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    temperatura_c: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    frequencia_cardiaca: Mapped[int | None] = mapped_column(nullable=True)
    frequencia_respiratoria: Mapped[int | None] = mapped_column(nullable=True)
    exame_fisico: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostico: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lista de prescricoes: [{"principio_ativo": "...", "dose": ..., ...}, ...]
    prescricoes: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    receita_url: Mapped[str | None] = mapped_column(String, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    animal: Mapped[Animal] = relationship()
