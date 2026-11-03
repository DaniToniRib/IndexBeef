"""Schemas Pydantic para dados geneticos (DEPs)."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class DadosGeneticosRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    animal_id: uuid.UUID
    programa: str | None = None
    safra: str | None = None
    deps: dict[str, Any] | None = None
    indice_programa: Decimal | None = None
    deca: int | None = None
    data_importacao: date | None = None
