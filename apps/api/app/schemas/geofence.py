from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from shapely.errors import GEOSException
from shapely.wkt import loads as wkt_loads

TipoGeofenceStr = Literal["pasto", "limite", "alerta", "curral"]
TipoEventoStr = Literal["entrada", "saida"]


class GeofenceBase(BaseModel):
    fazenda_id: uuid.UUID
    nome: str = Field(min_length=1)
    tipo: TipoGeofenceStr = "pasto"
    poligono_wkt: str
    ativa: bool = True
    descricao: str | None = None

    @field_validator("poligono_wkt")
    @classmethod
    def valida_wkt(cls, v: str) -> str:
        try:
            geom = wkt_loads(v)
        except (GEOSException, ValueError, TypeError) as e:
            raise ValueError(f"WKT invalido: {e}") from e
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            raise ValueError(
                f"geometria deve ser POLYGON ou MULTIPOLYGON (recebeu {geom.geom_type})",
            )
        if not geom.is_valid:
            raise ValueError("poligono invalido (verifique auto-intersecoes)")
        return v


class GeofenceCreate(GeofenceBase):
    pass


class GeofenceUpdate(BaseModel):
    nome: str | None = None
    tipo: TipoGeofenceStr | None = None
    poligono_wkt: str | None = None
    ativa: bool | None = None
    descricao: str | None = None


class GeofenceRead(GeofenceBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class EventoGeofenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    animal_id: uuid.UUID
    geofence_id: uuid.UUID
    tipo: TipoEventoStr
    timestamp: datetime
