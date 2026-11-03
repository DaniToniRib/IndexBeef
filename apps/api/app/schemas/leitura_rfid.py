from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normaliza_eid(v: str) -> str:
    return v.replace(" ", "").replace("-", "")


class LeituraRfidBase(BaseModel):
    dispositivo_id: uuid.UUID | None = None
    eid: str = Field(min_length=1, max_length=32)
    vid: str | None = None
    timestamp: datetime
    session: str | None = None
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)

    @field_validator("eid")
    @classmethod
    def normaliza(cls, v: str) -> str:
        return _normaliza_eid(v)


class LeituraRfidCreate(LeituraRfidBase):
    pass


class LeituraRfidRead(LeituraRfidBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    animal_id: uuid.UUID | None = None
    pareado_em: datetime | None = None


class LeituraRfidBatchCreate(BaseModel):
    leituras: list[LeituraRfidCreate] = Field(min_length=1)


class ImportacaoResultado(BaseModel):
    importadas: int
    pareadas: int
    erros: list[dict[str, str]] = []
