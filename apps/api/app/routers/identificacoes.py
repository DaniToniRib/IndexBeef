from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.identificacao_eletronica import IdentificacaoEletronica
from app.schemas.identificacao_eletronica import (
    IdentificacaoEletronicaCreate,
    IdentificacaoEletronicaRead,
    IdentificacaoEletronicaUpdate,
)

router = APIRouter(prefix="/identificacoes", tags=["identificacoes-eletronicas"])


@router.post(
    "", response_model=IdentificacaoEletronicaRead, status_code=status.HTTP_201_CREATED,
)
def criar(
    payload: IdentificacaoEletronicaCreate, db: Session = Depends(get_db),
) -> IdentificacaoEletronica:
    ident = IdentificacaoEletronica(**payload.model_dump())
    db.add(ident)
    db.commit()
    db.refresh(ident)
    return ident


@router.get("", response_model=list[IdentificacaoEletronicaRead])
def listar(
    animal_id: uuid.UUID | None = Query(default=None),
    eid: str | None = Query(default=None),
    ativo: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[IdentificacaoEletronica]:
    stmt = select(IdentificacaoEletronica)
    if animal_id is not None:
        stmt = stmt.where(IdentificacaoEletronica.animal_id == animal_id)
    if eid is not None:
        stmt = stmt.where(IdentificacaoEletronica.eid == eid)
    if ativo is not None:
        stmt = stmt.where(IdentificacaoEletronica.ativo == ativo)
    return list(db.scalars(stmt).all())


@router.get("/{ident_id}", response_model=IdentificacaoEletronicaRead)
def ler(ident_id: uuid.UUID, db: Session = Depends(get_db)) -> IdentificacaoEletronica:
    ident = db.get(IdentificacaoEletronica, ident_id)
    if ident is None:
        raise HTTPException(status_code=404, detail="identificacao nao encontrada")
    return ident


@router.patch("/{ident_id}", response_model=IdentificacaoEletronicaRead)
def atualizar(
    ident_id: uuid.UUID,
    payload: IdentificacaoEletronicaUpdate,
    db: Session = Depends(get_db),
) -> IdentificacaoEletronica:
    ident = db.get(IdentificacaoEletronica, ident_id)
    if ident is None:
        raise HTTPException(status_code=404, detail="identificacao nao encontrada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(ident, k, v)
    db.commit()
    db.refresh(ident)
    return ident


@router.delete("/{ident_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(ident_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    ident = db.get(IdentificacaoEletronica, ident_id)
    if ident is None:
        raise HTTPException(status_code=404, detail="identificacao nao encontrada")
    db.delete(ident)
    db.commit()
