from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import EstadoAtividadeGps

if TYPE_CHECKING:
    from app.models.animal import Animal
    from app.models.dispositivo import Dispositivo


class TelemetriaGps(SyncMixin, Base):
    """Ponto GPS enviado por um tracker (ver docs/11 §3).

    `latitude`/`longitude` em WGS84. Em producao com PostGIS adicionamos
    coluna Geometry(Point, 4326) e indice GiST — por ora mantemos como
    Numeric para portabilidade com SQLite nos testes.

    `atividade` conta picos do acelerometro na janela (padrao 1h) — base
    para deteccao de cio (ver Cowmed/SenseHub, docs/11 §3).
    """

    __tablename__ = "telemetria_gps"

    dispositivo_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("dispositivo.id", ondelete="SET NULL"), nullable=True,
    )
    animal_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="SET NULL"), nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    hdop: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    bateria_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperatura_c: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    atividade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[EstadoAtividadeGps | None] = mapped_column(
        SAEnum(EstadoAtividadeGps, name="estado_atividade_gps"), nullable=True,
    )
    rssi: Mapped[int | None] = mapped_column(Integer, nullable=True)

    dispositivo: Mapped[Dispositivo | None] = relationship()
    animal: Mapped[Animal | None] = relationship()
