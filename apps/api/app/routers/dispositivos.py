from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.dispositivo import Dispositivo
from app.schemas.dispositivo import (
    DispositivoCreate,
    DispositivoRead,
    DispositivoUpdate,
)

router = APIRouter(prefix="/dispositivos", tags=["dispositivos"])


@router.post("", response_model=DispositivoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: DispositivoCreate, db: Session = Depends(get_db)) -> Dispositivo:
    d = Dispositivo(**payload.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.get("", response_model=list[DispositivoRead])
def listar(
    fazenda_id: uuid.UUID | None = Query(default=None),
    tipo: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Dispositivo]:
    stmt = select(Dispositivo)
    if fazenda_id is not None:
        stmt = stmt.where(Dispositivo.fazenda_id == fazenda_id)
    if tipo is not None:
        stmt = stmt.where(Dispositivo.tipo == tipo)
    return list(db.scalars(stmt).all())


@router.get("/{disp_id}", response_model=DispositivoRead)
def ler(disp_id: uuid.UUID, db: Session = Depends(get_db)) -> Dispositivo:
    d = db.get(Dispositivo, disp_id)
    if d is None:
        raise HTTPException(status_code=404, detail="dispositivo nao encontrado")
    return d


@router.patch("/{disp_id}", response_model=DispositivoRead)
def atualizar(
    disp_id: uuid.UUID,
    payload: DispositivoUpdate,
    db: Session = Depends(get_db),
) -> Dispositivo:
    d = db.get(Dispositivo, disp_id)
    if d is None:
        raise HTTPException(status_code=404, detail="dispositivo nao encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/{disp_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(disp_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    d = db.get(Dispositivo, disp_id)
    if d is None:
        raise HTTPException(status_code=404, detail="dispositivo nao encontrado")
    db.delete(d)
    db.commit()
