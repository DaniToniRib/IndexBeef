from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EstadoAtividadeStr = Literal["grazing", "walking", "resting", "desconhecido"]


class TelemetriaGpsBase(BaseModel):
    dispositivo_id: uuid.UUID | None = None
    animal_id: uuid.UUID | None = None
    timestamp: datetime
    latitude: Decimal = Field(ge=-90, le=90)
    longitude: Decimal = Field(ge=-180, le=180)
    hdop: Decimal | None = Field(default=None, ge=0)
    bateria_pct: int | None = Field(default=None, ge=0, le=100)
    temperatura_c: Decimal | None = None
    atividade: int | None = Field(default=None, ge=0)
    estado: EstadoAtividadeStr | None = None
    rssi: int | None = None


class TelemetriaGpsCreate(TelemetriaGpsBase):
    pass


class TelemetriaGpsRead(TelemetriaGpsBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class TelemetriaGpsBatchCreate(BaseModel):
    pontos: list[TelemetriaGpsCreate] = Field(min_length=1)


class TelemetriaIngestaoResultado(BaseModel):
    importados: int
    eventos_geofence_gerados: int
    alertas: list[dict[str, str]] = []
