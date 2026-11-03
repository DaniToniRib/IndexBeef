"""Schemas Pydantic para exames andrologicos."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import ResultadoAndrologico


class ExameAndrologicoCreate(BaseModel):
    animal_id: uuid.UUID
    data: date
    perimetro_escrotal_cm: Decimal | None = None
    resultado: ResultadoAndrologico | None = None
    veterinario: str | None = None
    observacoes: str | None = None


class ExameAndrologicoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    animal_id: uuid.UUID
    data: date
    perimetro_escrotal_cm: Decimal | None = None
    resultado: ResultadoAndrologico | None = None
    veterinario: str | None = None
    observacoes: str | None = None
