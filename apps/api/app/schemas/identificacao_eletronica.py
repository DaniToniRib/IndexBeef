from __future__ import annotations

import re
import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ModoRfidStr = Literal["FDX_B", "HDX"]

_RE_EID_15 = re.compile(r"^\d{15}$")


class IdentificacaoEletronicaBase(BaseModel):
    animal_id: uuid.UUID
    eid: str = Field(min_length=1, max_length=32)
    vid: str | None = None
    modo: ModoRfidStr = "FDX_B"
    fabricante: str | None = None
    ativo: bool = True
    ativo_desde: date
    inativo_desde: date | None = None
    motivo_troca: str | None = None

    @field_validator("eid")
    @classmethod
    def valida_eid(cls, v: str) -> str:
        v2 = v.replace(" ", "").replace("-", "")
        # Padrao ISO 11784 brasileiro: 15 digitos comecando com 076.
        # Permitimos tambem outros formatos para nao travar imports de bastao
        # (ex: "982 000012345678" vem com prefixo de fabricante).
        if _RE_EID_15.match(v2) and not v2.startswith("076"):
            # 15 digitos mas nao-BR: aceita com warning silencioso (log cliente)
            return v2
        return v2


class IdentificacaoEletronicaCreate(IdentificacaoEletronicaBase):
    pass


class IdentificacaoEletronicaUpdate(BaseModel):
    vid: str | None = None
    fabricante: str | None = None
    ativo: bool | None = None
    inativo_desde: date | None = None
    motivo_troca: str | None = None


class IdentificacaoEletronicaRead(IdentificacaoEletronicaBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
