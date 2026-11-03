from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.fazenda import Fazenda
from app.schemas.fazenda import FazendaCreate, FazendaRead, FazendaUpdate

router = APIRouter(prefix="/fazendas", tags=["fazendas"])


@router.post("", response_model=FazendaRead, status_code=status.HTTP_201_CREATED)
def criar(payload: FazendaCreate, db: Session = Depends(get_db)) -> Fazenda:
    f = Fazenda(**payload.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.get("", response_model=list[FazendaRead])
def listar(db: Session = Depends(get_db)) -> list[Fazenda]:
    return list(db.scalars(select(Fazenda).order_by(Fazenda.nome)).all())


@router.get("/{fazenda_id}", response_model=FazendaRead)
def ler(fazenda_id: uuid.UUID, db: Session = Depends(get_db)) -> Fazenda:
    f = db.get(Fazenda, fazenda_id)
    if f is None:
        raise HTTPException(status_code=404, detail="fazenda nao encontrada")
    return f


@router.patch("/{fazenda_id}", response_model=FazendaRead)
def atualizar(
    fazenda_id: uuid.UUID,
    payload: FazendaUpdate,
    db: Session = Depends(get_db),
) -> Fazenda:
    f = db.get(Fazenda, fazenda_id)
    if f is None:
        raise HTTPException(status_code=404, detail="fazenda nao encontrada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    return f


@router.delete("/{fazenda_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(fazenda_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    f = db.get(Fazenda, fazenda_id)
    if f is None:
        raise HTTPException(status_code=404, detail="fazenda nao encontrada")
    db.delete(f)
    db.commit()
