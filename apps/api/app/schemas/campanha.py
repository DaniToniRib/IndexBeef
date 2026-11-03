from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

TipoAplicacaoStr = Literal["vacina", "vermifugo", "terapeutico"]
StatusCampanhaStr = Literal["planejada", "em_andamento", "concluida", "cancelada"]


class CampanhaBase(BaseModel):
    fazenda_id: uuid.UUID
    nome: str
    tipo: TipoAplicacaoStr
    data_inicio: date
    data_fim: date | None = None
    protocolo: str | None = None
    status: StatusCampanhaStr = "planejada"


class CampanhaCreate(CampanhaBase):
    pass


class CampanhaUpdate(BaseModel):
    nome: str | None = None
    data_fim: date | None = None
    protocolo: str | None = None
    status: StatusCampanhaStr | None = None


class CampanhaRead(CampanhaBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
