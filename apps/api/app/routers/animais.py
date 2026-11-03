from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.animal import Animal
from app.schemas.animal import (
    AnimalCreate,
    AnimalHistorico,
    AnimalRead,
    AnimalUpdate,
)
from app.services.historico import consolidar_historico

router = APIRouter(prefix="/animais", tags=["animais"])


@router.post("", response_model=AnimalRead, status_code=status.HTTP_201_CREATED)
def criar(payload: AnimalCreate, db: Session = Depends(get_db)) -> Animal:
    animal = Animal(**payload.model_dump())
    db.add(animal)
    db.commit()
    db.refresh(animal)
    return animal


@router.get("", response_model=list[AnimalRead])
def listar(
    fazenda_id: uuid.UUID | None = Query(default=None),
    lote_id: uuid.UUID | None = Query(default=None),
    brinco: str | None = Query(default=None),
    rgn: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Animal]:
    stmt = select(Animal)
    if fazenda_id is not None:
        stmt = stmt.where(Animal.fazenda_id == fazenda_id)
    if lote_id is not None:
        stmt = stmt.where(Animal.lote_id == lote_id)
    if brinco is not None:
        stmt = stmt.where(Animal.brinco == brinco)
    if rgn is not None:
        stmt = stmt.where(Animal.rgn == rgn)
    return list(db.scalars(stmt.order_by(Animal.brinco)).all())


@router.get("/{animal_id}", response_model=AnimalRead)
def ler(animal_id: uuid.UUID, db: Session = Depends(get_db)) -> Animal:
    a = db.get(Animal, animal_id)
    if a is None:
        raise HTTPException(status_code=404, detail="animal nao encontrado")
    return a


@router.patch("/{animal_id}", response_model=AnimalRead)
def atualizar(
    animal_id: uuid.UUID,
    payload: AnimalUpdate,
    db: Session = Depends(get_db),
) -> Animal:
    a = db.get(Animal, animal_id)
    if a is None:
        raise HTTPException(status_code=404, detail="animal nao encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(animal_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    a = db.get(Animal, animal_id)
    if a is None:
        raise HTTPException(status_code=404, detail="animal nao encontrado")
    db.delete(a)
    db.commit()


@router.get("/{animal_id}/historico", response_model=AnimalHistorico)
def historico(animal_id: uuid.UUID, db: Session = Depends(get_db)) -> AnimalHistorico:
    try:
        return consolidar_historico(db, animal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
