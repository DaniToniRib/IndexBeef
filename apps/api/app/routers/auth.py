"""Router de autenticacao — registro, login e perfil (Fase 5).

Endpoints novos e opcionais: nao modifica nenhum endpoint existente.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import criar_token, decodificar_token, hash_senha, verificar_senha
from app.core.db import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import TokenResponse, UsuarioLogin, UsuarioRead, UsuarioRegistrar

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer(auto_error=False)


def _usuario_atual(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependencia: extrai e valida o JWT; levanta 401 se invalido."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token ausente")
    payload = decodificar_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token invalido")
    try:
        usuario_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token invalido")
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="usuario nao encontrado")
    return usuario


@router.post("/registrar", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def registrar(payload: UsuarioRegistrar, db: Session = Depends(get_db)) -> Usuario:
    """Cria novo usuario. Retorna 409 se email ja existir."""
    existente = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if existente is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email ja cadastrado")
    usuario = Usuario(
        email=payload.email,
        nome=payload.nome,
        senha_hash=hash_senha(payload.senha),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=TokenResponse)
def login(payload: UsuarioLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """Autentica usuario e retorna JWT. Retorna 401 se credenciais invalidas."""
    usuario = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if usuario is None or not verificar_senha(payload.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="credenciais invalidas",
        )
    token = criar_token(str(usuario.id), usuario.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioRead)
def me(usuario: Usuario = Depends(_usuario_atual)) -> Usuario:
    """Retorna dados do usuario autenticado pelo JWT."""
    return usuario
