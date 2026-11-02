"""Base declarativa + mixins obrigatorios (ver docs/06-modelo-de-dados.md).

Todas as tabelas tem:
- id UUID PK (gerado na origem; o cliente pode enviar ou cair no default uuid4)
- criado_em, atualizado_em (timestamp with tz)
- origem_estacao (identifica a estacao de campo que criou o registro)
- sincronizado_em (timestamp do envio para a nuvem; nulo = ainda nao sincronizado)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SyncMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    origem_estacao: Mapped[str | None] = mapped_column(nullable=True)
    sincronizado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
