from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.pesagem import Pesagem
from app.schemas.pesagem import PesagemCreate, PesagemRead

router = APIRouter(prefix="/pesagens", tags=["pesagens"])


@router.post("", response_model=PesagemRead, status_code=status.HTTP_201_CREATED)
def criar(payload: PesagemCreate, db: Session = Depends(get_db)) -> Pesagem:
    p = Pesagem(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("", response_model=list[PesagemRead])
def listar(
    animal_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Pesagem]:
    stmt = select(Pesagem).order_by(Pesagem.data)
    if animal_id is not None:
        stmt = stmt.where(Pesagem.animal_id == animal_id)
    return list(db.scalars(stmt).all())


@router.get("/{pesagem_id}", response_model=PesagemRead)
def ler(pesagem_id: uuid.UUID, db: Session = Depends(get_db)) -> Pesagem:
    p = db.get(Pesagem, pesagem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="pesagem nao encontrada")
    return p


@router.delete("/{pesagem_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(pesagem_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    p = db.get(Pesagem, pesagem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="pesagem nao encontrada")
    db.delete(p)
    db.commit()
