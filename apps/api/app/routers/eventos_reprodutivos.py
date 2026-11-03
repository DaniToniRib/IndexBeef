"""Router de eventos reprodutivos."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.animal import Animal
from app.models.evento_reprodutivo import EventoReprodutivo
from app.schemas.evento_reprodutivo import EventoReprodutivoCreate, EventoReprodutivoRead

router = APIRouter(prefix="/eventos-reprodutivos", tags=["eventos-reprodutivos"])


@router.post(
    "",
    response_model=EventoReprodutivoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_evento(
    payload: EventoReprodutivoCreate, db: Session = Depends(get_db),
) -> EventoReprodutivo:
    animal = db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="animal nao encontrado")
    evento = EventoReprodutivo(**payload.model_dump())
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


@router.get("", response_model=list[EventoReprodutivoRead])
def listar_eventos(
    animal_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> list[EventoReprodutivo]:
    stmt = (
        select(EventoReprodutivo)
        .where(EventoReprodutivo.animal_id == animal_id)
        .order_by(EventoReprodutivo.data.desc())
    )
    return list(db.scalars(stmt).all())
