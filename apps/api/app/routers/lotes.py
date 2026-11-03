from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.lote import Lote
from app.schemas.lote import LoteCreate, LoteRead, LoteUpdate

router = APIRouter(prefix="/lotes", tags=["lotes"])


@router.post("", response_model=LoteRead, status_code=status.HTTP_201_CREATED)
def criar(payload: LoteCreate, db: Session = Depends(get_db)) -> Lote:
    lote = Lote(**payload.model_dump())
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return lote


@router.get("", response_model=list[LoteRead])
def listar(
    fazenda_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Lote]:
    stmt = select(Lote).order_by(Lote.nome)
    if fazenda_id is not None:
        stmt = stmt.where(Lote.fazenda_id == fazenda_id)
    return list(db.scalars(stmt).all())


@router.get("/{lote_id}", response_model=LoteRead)
def ler(lote_id: uuid.UUID, db: Session = Depends(get_db)) -> Lote:
    lote = db.get(Lote, lote_id)
    if lote is None:
        raise HTTPException(status_code=404, detail="lote nao encontrado")
    return lote


@router.patch("/{lote_id}", response_model=LoteRead)
def atualizar(
    lote_id: uuid.UUID, payload: LoteUpdate, db: Session = Depends(get_db),
) -> Lote:
    lote = db.get(Lote, lote_id)
    if lote is None:
        raise HTTPException(status_code=404, detail="lote nao encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(lote, k, v)
    db.commit()
    db.refresh(lote)
    return lote


@router.delete("/{lote_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(lote_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    lote = db.get(Lote, lote_id)
    if lote is None:
        raise HTTPException(status_code=404, detail="lote nao encontrado")
    db.delete(lote)
    db.commit()
