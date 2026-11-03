from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.atendimento_veterinario import AtendimentoVeterinario
from app.schemas.atendimento_veterinario import (
    AtendimentoVeterinarioCreate,
    AtendimentoVeterinarioRead,
)

router = APIRouter(prefix="/atendimentos-veterinarios", tags=["atendimentos-vet"])


@router.post(
    "", response_model=AtendimentoVeterinarioRead, status_code=status.HTTP_201_CREATED,
)
def criar(
    payload: AtendimentoVeterinarioCreate, db: Session = Depends(get_db),
) -> AtendimentoVeterinario:
    a = AtendimentoVeterinario(**payload.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.get("", response_model=list[AtendimentoVeterinarioRead])
def listar(
    animal_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AtendimentoVeterinario]:
    stmt = select(AtendimentoVeterinario).order_by(
        AtendimentoVeterinario.data_hora.desc(),
    )
    if animal_id is not None:
        stmt = stmt.where(AtendimentoVeterinario.animal_id == animal_id)
    return list(db.scalars(stmt).all())


@router.get("/{atendimento_id}", response_model=AtendimentoVeterinarioRead)
def ler(
    atendimento_id: uuid.UUID, db: Session = Depends(get_db),
) -> AtendimentoVeterinario:
    a = db.get(AtendimentoVeterinario, atendimento_id)
    if a is None:
        raise HTTPException(status_code=404, detail="atendimento nao encontrado")
    return a
