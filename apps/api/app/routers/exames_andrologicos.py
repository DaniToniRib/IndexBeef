"""Router de exames andrologicos."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.animal import Animal
from app.models.exame_andrologico import ExameAndrologico
from app.schemas.exame_andrologico import ExameAndrologicoCreate, ExameAndrologicoRead

router = APIRouter(prefix="/exames-andrologicos", tags=["exames-andrologicos"])


@router.post(
    "",
    response_model=ExameAndrologicoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_exame(
    payload: ExameAndrologicoCreate, db: Session = Depends(get_db),
) -> ExameAndrologico:
    animal = db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="animal nao encontrado")
    exame = ExameAndrologico(**payload.model_dump())
    db.add(exame)
    db.commit()
    db.refresh(exame)
    return exame


@router.get("", response_model=list[ExameAndrologicoRead])
def listar_exames(
    animal_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> list[ExameAndrologico]:
    stmt = (
        select(ExameAndrologico)
        .where(ExameAndrologico.animal_id == animal_id)
        .order_by(ExameAndrologico.data.desc())
    )
    return list(db.scalars(stmt).all())
