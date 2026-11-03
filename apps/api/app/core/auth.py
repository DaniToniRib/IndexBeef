"""Autenticacao JWT + bcrypt para o IndexBeef (Fase 5).

Segredo e algoritmo configurados aqui; em producao usar variavel de ambiente
INDEXBEEF_SECRET_KEY.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

SECRET_KEY: str = os.getenv("INDEXBEEF_SECRET_KEY", "dev-secret-change-in-production-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 dias


def hash_senha(senha: str) -> str:
    """Retorna hash bcrypt da senha."""
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Retorna True se a senha corresponde ao hash."""
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())


def criar_token(usuario_id: str, email: str) -> str:
    """Cria JWT com sub=usuario_id, email e exp."""
    payload = {
        "sub": usuario_id,
        "email": email,
        "exp": datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict | None:
    """Decodifica o JWT; retorna None se invalido ou expirado."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
