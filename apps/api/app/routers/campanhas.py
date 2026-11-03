from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.campanha import Campanha
from app.schemas.campanha import CampanhaCreate, CampanhaRead, CampanhaUpdate

router = APIRouter(prefix="/campanhas", tags=["campanhas"])


@router.post("", response_model=CampanhaRead, status_code=status.HTTP_201_CREATED)
def criar(payload: CampanhaCreate, db: Session = Depends(get_db)) -> Campanha:
    c = Campanha(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("", response_model=list[CampanhaRead])
def listar(
    fazenda_id: uuid.UUID | None = Query(default=None),
    tipo: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Campanha]:
    stmt = select(Campanha).order_by(Campanha.data_inicio.desc())
    if fazenda_id is not None:
        stmt = stmt.where(Campanha.fazenda_id == fazenda_id)
    if tipo is not None:
        stmt = stmt.where(Campanha.tipo == tipo)
    return list(db.scalars(stmt).all())


@router.get("/{campanha_id}", response_model=CampanhaRead)
def ler(campanha_id: uuid.UUID, db: Session = Depends(get_db)) -> Campanha:
    c = db.get(Campanha, campanha_id)
    if c is None:
        raise HTTPException(status_code=404, detail="campanha nao encontrada")
    return c


@router.patch("/{campanha_id}", response_model=CampanhaRead)
def atualizar(
    campanha_id: uuid.UUID,
    payload: CampanhaUpdate,
    db: Session = Depends(get_db),
) -> Campanha:
    c = db.get(Campanha, campanha_id)
    if c is None:
        raise HTTPException(status_code=404, detail="campanha nao encontrada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c
