"""Schemas Pydantic para o endpoint de modelo_versao."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ModeloVersaoCreate(BaseModel):
    nome: str
    versao: str
    metricas: dict[str, Any] | None = None
    artefato_url: str | None = None
    ativo: bool = False
    descricao: str | None = None


class ModeloVersaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    versao: str
    metricas: dict[str, Any] | None
    artefato_url: str | None
    ativo: bool
    descricao: str | None
    criado_em: datetime
    atualizado_em: datetime
