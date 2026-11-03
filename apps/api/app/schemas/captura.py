from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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
