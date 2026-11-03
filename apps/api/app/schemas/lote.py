from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

CategoriaLoteStr = Literal["bezerro", "garrote", "novilha", "matriz", "touro"]


class LoteBase(BaseModel):
    fazenda_id: uuid.UUID
    nome: str
    categoria: CategoriaLoteStr


class LoteCreate(LoteBase):
    pass


class LoteUpdate(BaseModel):
    nome: str | None = None
    categoria: CategoriaLoteStr | None = None


class LoteRead(LoteBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
