from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.aplicacao_sanitaria import AplicacaoSanitaria
from app.schemas.aplicacao_sanitaria import (
    AplicacaoSanitariaCreate,
    AplicacaoSanitariaRead,
)

router = APIRouter(prefix="/aplicacoes-sanitarias", tags=["aplicacoes-sanitarias"])


@router.post(
    "", response_model=AplicacaoSanitariaRead, status_code=status.HTTP_201_CREATED,
)
def criar(
    payload: AplicacaoSanitariaCreate, db: Session = Depends(get_db),
) -> AplicacaoSanitariaRead:
    a = AplicacaoSanitaria(**payload.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return AplicacaoSanitariaRead.from_model(a)


@router.get("", response_model=list[AplicacaoSanitariaRead])
def listar(
    animal_id: uuid.UUID | None = Query(default=None),
    campanha_id: uuid.UUID | None = Query(default=None),
    tipo: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AplicacaoSanitariaRead]:
    stmt = select(AplicacaoSanitaria).order_by(AplicacaoSanitaria.data.desc())
    if animal_id is not None:
        stmt = stmt.where(AplicacaoSanitaria.animal_id == animal_id)
    if campanha_id is not None:
        stmt = stmt.where(AplicacaoSanitaria.campanha_id == campanha_id)
    if tipo is not None:
        stmt = stmt.where(AplicacaoSanitaria.tipo == tipo)
    return [AplicacaoSanitariaRead.from_model(a) for a in db.scalars(stmt).all()]


@router.get("/{aplicacao_id}", response_model=AplicacaoSanitariaRead)
def ler(
    aplicacao_id: uuid.UUID, db: Session = Depends(get_db),
) -> AplicacaoSanitariaRead:
    a = db.get(AplicacaoSanitaria, aplicacao_id)
    if a is None:
        raise HTTPException(status_code=404, detail="aplicacao nao encontrada")
    return AplicacaoSanitariaRead.from_model(a)


@router.delete("/{aplicacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(aplicacao_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    a = db.get(AplicacaoSanitaria, aplicacao_id)
    if a is None:
        raise HTTPException(status_code=404, detail="aplicacao nao encontrada")
    db.delete(a)
    db.commit()
