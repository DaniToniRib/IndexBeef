from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import TipoFazenda

if TYPE_CHECKING:
    from app.models.dispositivo import Dispositivo
    from app.models.lote import Lote


class Fazenda(SyncMixin, Base):
    __tablename__ = "fazenda"

    nome: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[TipoFazenda] = mapped_column(
        SAEnum(TipoFazenda, name="tipo_fazenda"),
        nullable=False,
        default=TipoFazenda.fazenda,
    )
    municipio: Mapped[str | None] = mapped_column(String, nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    bioma: Mapped[str | None] = mapped_column(String, nullable=True)
    # Posicao da sede (ponto simples). Para geofences/trajetos usamos PostGIS
    # em telemetria_gps e geofence (Fase D).
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    area_hectares: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    codigo_sisbov: Mapped[str | None] = mapped_column(String, nullable=True)
    inscricao_estadual: Mapped[str | None] = mapped_column(String, nullable=True)

    lotes: Mapped[list[Lote]] = relationship(
        back_populates="fazenda", cascade="all, delete-orphan",
    )
    dispositivos: Mapped[list[Dispositivo]] = relationship(
        back_populates="fazenda", cascade="all, delete-orphan",
    )
