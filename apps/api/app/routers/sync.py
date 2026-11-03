"""Router de sincronizacao fazenda ↔ nuvem (Fase 5).

POST /sync/push  — estacao envia registros para a nuvem (upsert)
GET  /sync/pull  — estacao busca registros atualizados na nuvem
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    Animal,
    Avaliacao,
    Captura,
    DadosGeneticos,
    EscoreAvaliacao,
    EventoReprodutivo,
    ExameAndrologico,
    MedidaAvaliacao,
    Pesagem,
)

router = APIRouter(prefix="/sync", tags=["sync"])

# Mapeamento nome_tabela -> classe SQLAlchemy
_TABELAS: dict[str, type] = {
    "animal": Animal,
    "pesagem": Pesagem,
    "avaliacao": Avaliacao,
    "captura": Captura,
    "escore_avaliacao": EscoreAvaliacao,
    "medida_avaliacao": MedidaAvaliacao,
    "evento_reprodutivo": EventoReprodutivo,
    "exame_andrologico": ExameAndrologico,
    "dados_geneticos": DadosGeneticos,
}

_TODAS_TABELAS = list(_TABELAS.keys())


def _obj_para_dict(obj: Any) -> dict[str, Any]:
    """Converte objeto SQLAlchemy para dict serializavel (UUID e datetime para str)."""
    resultado: dict[str, Any] = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, uuid.UUID):
            val = str(val)
        elif isinstance(val, datetime):
            val = val.isoformat()
        elif hasattr(val, "isoformat"):  # date
            val = val.isoformat()
        elif hasattr(val, "__class__") and hasattr(val.__class__, "__mro__"):
            # enum
            if hasattr(val, "value"):
                val = val.value
        resultado[col.name] = val
    return resultado


def _coerce_uuid(val: Any) -> uuid.UUID | None:
    """Converte str ou UUID para uuid.UUID; retorna None se invalido."""
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


def _coerce_datetime(val: Any) -> datetime | None:
    """Converte str ISO para datetime com tz; retorna None se invalido/None."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        dt = datetime.fromisoformat(str(val))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (ValueError, TypeError):
        return None


def _coerce_date(val: Any) -> date | None:
    """Converte str ISO para date; retorna None se invalido/None."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None


def _dict_para_obj(classe: type, dados: dict[str, Any], db: Session) -> Any:
    """Upsert: atualiza registro existente ou cria novo. Ultimo atualizado_em vence."""
    id_val = _coerce_uuid(dados.get("id"))
    existente = db.get(classe, id_val) if id_val else None

    # Detectar colunas por tipo para coerção
    uuid_cols = {
        c.name
        for c in classe.__table__.columns
        if hasattr(c.type, "__class__") and c.type.__class__.__name__ == "Uuid"
    }
    datetime_cols = {
        c.name
        for c in classe.__table__.columns
        if hasattr(c.type, "__class__") and c.type.__class__.__name__ == "DateTime"
    }
    date_cols = {
        c.name
        for c in classe.__table__.columns
        if hasattr(c.type, "__class__") and c.type.__class__.__name__ == "Date"
    }

    def _preparar_valor(col_name: str, val: Any) -> Any:
        if col_name in uuid_cols:
            return _coerce_uuid(val)
        if col_name in datetime_cols:
            return _coerce_datetime(val)
        if col_name in date_cols:
            return _coerce_date(val)
        return val

    if existente is not None:
        # Atualizar campos
        cols = {c.name for c in classe.__table__.columns}
        for k, v in dados.items():
            if k in cols and k not in ("id", "criado_em"):
                setattr(existente, k, _preparar_valor(k, v))
        return existente
    else:
        obj = classe()
        cols = {c.name for c in classe.__table__.columns}
        for k, v in dados.items():
            if k in cols:
                setattr(obj, k, _preparar_valor(k, v))
        db.add(obj)
        return obj


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RegistroSync(BaseModel):
    tabela: str
    dados: dict[str, Any]


class PushPayload(BaseModel):
    estacao_id: str
    registros: list[RegistroSync]


class PushResponse(BaseModel):
    processados: int
    erros: list[str]
    sincronizado_em: str


class PullResponse(BaseModel):
    registros: list[dict[str, Any]]
    total: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/push", response_model=PushResponse)
def push(payload: PushPayload, db: Session = Depends(get_db)) -> PushResponse:
    """Recebe registros de uma estacao de campo e faz upsert no banco."""
    processados = 0
    erros: list[str] = []
    agora = datetime.now(UTC)

    for reg in payload.registros:
        if reg.tabela not in _TABELAS:
            raise HTTPException(
                status_code=422,
                detail=f"tabela '{reg.tabela}' nao suportada para sync",
            )
        try:
            classe = _TABELAS[reg.tabela]
            obj = _dict_para_obj(classe, reg.dados, db)
            obj.sincronizado_em = agora
            db.flush()
            processados += 1
        except Exception as exc:
            erros.append(f"{reg.tabela}/{reg.dados.get('id', '?')}: {exc!s}")

    db.commit()
    return PushResponse(
        processados=processados,
        erros=erros,
        sincronizado_em=agora.isoformat(),
    )


@router.get("/pull", response_model=PullResponse)
def pull(
    estacao_id: str = Query(...),
    desde: datetime = Query(...),
    tabelas: str = Query(default=",".join(_TODAS_TABELAS)),
    db: Session = Depends(get_db),
) -> PullResponse:
    """Retorna registros atualizados desde `desde` para as tabelas solicitadas."""
    nomes_tabelas = [t.strip() for t in tabelas.split(",") if t.strip()]
    registros: list[dict[str, Any]] = []

    for nome in nomes_tabelas:
        if nome not in _TABELAS:
            continue
        classe = _TABELAS[nome]
        stmt = (
            select(classe)
            .where(classe.atualizado_em > desde)
            .limit(500)
        )
        objetos = db.scalars(stmt).all()
        for obj in objetos:
            registros.append({"tabela": nome, "dados": _obj_para_dict(obj)})

    return PullResponse(registros=registros, total=len(registros))
