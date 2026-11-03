from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

TipoDispositivoStr = Literal[
    "balanca", "bastao_rfid", "antena_rfid_brete", "gps_tracker", "camera", "outro",
]
StatusDispositivoStr = Literal["ativo", "inativo", "manutencao"]


class DispositivoBase(BaseModel):
    fazenda_id: uuid.UUID
    tipo: TipoDispositivoStr
    modelo: str | None = None
    fabricante: str | None = None
    numero_serie: str | None = None
    data_instalacao: date | None = None
    status: StatusDispositivoStr = "ativo"
    config: dict[str, Any] | None = None


class DispositivoCreate(DispositivoBase):
    pass


class DispositivoUpdate(BaseModel):
    modelo: str | None = None
    fabricante: str | None = None
    numero_serie: str | None = None
    data_instalacao: date | None = None
    status: StatusDispositivoStr | None = None
    config: dict[str, Any] | None = None


class DispositivoRead(DispositivoBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
