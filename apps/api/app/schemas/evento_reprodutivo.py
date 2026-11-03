"""Schemas Pydantic para eventos reprodutivos."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import TipoEventoReprodutivo


class EventoReprodutivoCreate(BaseModel):
    animal_id: uuid.UUID
    tipo: TipoEventoReprodutivo
    data: date
    resultado: str | None = None
    dias_gestacao: int | None = None
    touro_id: uuid.UUID | None = None
    bezerro_id: uuid.UUID | None = None
    peso_desmama_bezerro: Decimal | None = None
    observacoes: str | None = None


class EventoReprodutivoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    animal_id: uuid.UUID
    tipo: TipoEventoReprodutivo
    data: date
    resultado: str | None = None
    dias_gestacao: int | None = None
    touro_id: uuid.UUID | None = None
    bezerro_id: uuid.UUID | None = None
    peso_desmama_bezerro: Decimal | None = None
    observacoes: str | None = None
