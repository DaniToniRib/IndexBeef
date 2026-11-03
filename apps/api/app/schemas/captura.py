from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CapturaCreate(BaseModel):
    avaliacao_id: uuid.UUID
    arquivo_url: str
    tipo: Literal["foto", "ao_vivo", "video"] = "foto"
    vista: Literal["lateral", "traseira", "dorsal", "frontal"] = "lateral"


class CapturaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    avaliacao_id: uuid.UUID
    tipo: str
    vista: str
    arquivo_url: str
    dispositivo: str | None = None
    px_por_cm: Decimal | None = None
    criado_em: datetime


class FrameExtraidoResponse(BaseModel):
    frame_url: str
    tipo_mime: str = "image/jpeg"
