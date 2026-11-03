from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

OrigemPesagemStr = Literal["balanca", "estimado", "fita"]


class PesagemBase(BaseModel):
    animal_id: uuid.UUID
    data: date
    peso_kg: Decimal = Field(gt=0)
    origem: OrigemPesagemStr
    avaliacao_id: uuid.UUID | None = None
    dispositivo_id: uuid.UUID | None = None


class PesagemCreate(PesagemBase):
    pass


class PesagemRead(PesagemBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
