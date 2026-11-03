from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TipoFazendaStr = Literal["fazenda", "sitio", "retiro", "outro"]


class FazendaBase(BaseModel):
    nome: str
    tipo: TipoFazendaStr = "fazenda"
    municipio: str | None = None
    uf: str | None = Field(default=None, max_length=2)
    bioma: str | None = None
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    area_hectares: Decimal | None = Field(default=None, ge=0)
    codigo_sisbov: str | None = None
    inscricao_estadual: str | None = None


class FazendaCreate(FazendaBase):
    pass


class FazendaUpdate(BaseModel):
    nome: str | None = None
    tipo: TipoFazendaStr | None = None
    municipio: str | None = None
    uf: str | None = Field(default=None, max_length=2)
    bioma: str | None = None
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    area_hectares: Decimal | None = Field(default=None, ge=0)
    codigo_sisbov: str | None = None
    inscricao_estadual: str | None = None


class FazendaRead(FazendaBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
