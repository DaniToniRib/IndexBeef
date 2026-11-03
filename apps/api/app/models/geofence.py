from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import TipoGeofence

if TYPE_CHECKING:
    from app.models.evento_geofence import EventoGeofence
    from app.models.fazenda import Fazenda


class Geofence(SyncMixin, Base):
    """Cerca virtual: poligono WGS84 em WKT (ver docs/11 §3).

    `poligono_wkt` guarda a string WKT (POLYGON((lon lat, ...))) por ora.
    Em producao com PostGIS troca para Geometry(POLYGON, 4326) + indice
    GiST para queries ST_Contains eficientes. Shapely parseia WKT
    tanto em dev quanto em prod.
    """

    __tablename__ = "geofence"

    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False,
    )
    nome: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[TipoGeofence] = mapped_column(
        SAEnum(TipoGeofence, name="tipo_geofence"),
        nullable=False,
        default=TipoGeofence.pasto,
    )
    poligono_wkt: Mapped[str] = mapped_column(Text, nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)

    fazenda: Mapped[Fazenda] = relationship()
    eventos: Mapped[list[EventoGeofence]] = relationship(
        back_populates="geofence", cascade="all, delete-orphan",
    )
