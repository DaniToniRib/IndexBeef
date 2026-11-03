from __future__ import annotations

import re
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_RE_CRMV = re.compile(r"^[A-Za-z]{2}[-\s]?\d{3,7}$")


class AtendimentoVeterinarioBase(BaseModel):
    animal_id: uuid.UUID
    data_hora: datetime
    veterinario_nome: str = Field(min_length=1)
    veterinario_crmv: str
    motivo: str = Field(min_length=1)
    queixa: str | None = None
    peso_estimado_kg: Decimal | None = Field(default=None, gt=0)
    temperatura_c: Decimal | None = Field(default=None, gt=0)
    frequencia_cardiaca: int | None = Field(default=None, gt=0)
    frequencia_respiratoria: int | None = Field(default=None, gt=0)
    exame_fisico: str | None = None
    diagnostico: str | None = None
    prescricoes: list[dict[str, Any]] | None = None
    receita_url: str | None = None
    observacoes: str | None = None

    @field_validator("veterinario_crmv")
    @classmethod
    def valida_crmv(cls, v: str) -> str:
        if not _RE_CRMV.match(v):
            raise ValueError(
                f"CRMV invalido: {v!r} (formato esperado: 'UF-NNNNN', ex: 'SP-12345')",
            )
        return v


class AtendimentoVeterinarioCreate(AtendimentoVeterinarioBase):
    pass


class AtendimentoVeterinarioRead(AtendimentoVeterinarioBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
