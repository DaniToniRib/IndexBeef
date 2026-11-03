"""Schemas Pydantic para autenticacao e usuarios."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UsuarioRegistrar(BaseModel):
    email: str
    nome: str
    senha: str


class UsuarioLogin(BaseModel):
    email: str
    senha: str


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    nome: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
