from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.evento_geofence import EventoGeofence
from app.models.geofence import Geofence
from app.models.telemetria_gps import TelemetriaGps
from app.schemas.geofence import (
    EventoGeofenceRead,
    GeofenceCreate,
    GeofenceRead,
    GeofenceUpdate,
)
from app.schemas.telemetria_gps import (
    TelemetriaGpsBatchCreate,
    TelemetriaGpsRead,
    TelemetriaIngestaoResultado,
)
from app.services.geofence_service import detectar_alertas, processar_ponto

router = APIRouter(prefix="", tags=["gps"])


# ---------- Telemetria GPS ----------

@router.post(
    "/gps/pontos",
    response_model=TelemetriaIngestaoResultado,
    status_code=status.HTTP_201_CREATED,
)
def ingerir_pontos(
    payload: TelemetriaGpsBatchCreate, db: Session = Depends(get_db),
) -> TelemetriaIngestaoResultado:
    pontos_novos: list[TelemetriaGps] = []
    for p in payload.pontos:
        ponto = TelemetriaGps(**p.model_dump())
        db.add(ponto)
        pontos_novos.append(ponto)
    db.flush()

    # Para processar eventos de geofence, carregamos geofences ativas das
    # fazendas envolvidas uma unica vez.
    fazenda_ids: set[uuid.UUID] = set()
    for ponto in pontos_novos:
        if ponto.animal_id is not None and ponto.animal is not None:
            fazenda_ids.add(ponto.animal.fazenda_id)
    geofences = (
        list(
            db.scalars(
                select(Geofence)
                .where(Geofence.fazenda_id.in_(fazenda_ids))
                .where(Geofence.ativa.is_(True)),
            ).all(),
        )
        if fazenda_ids
        else []
    )

    eventos_total = 0
    alertas: list[dict[str, str]] = []
    for ponto in pontos_novos:
        eventos = processar_ponto(db, ponto, geofences)
        eventos_total += len(eventos)
        alertas.extend(detectar_alertas(ponto))
    db.commit()

    return TelemetriaIngestaoResultado(
        importados=len(pontos_novos),
        eventos_geofence_gerados=eventos_total,
        alertas=alertas,
    )


@router.get("/gps/pontos", response_model=list[TelemetriaGpsRead])
def listar_pontos(
    animal_id: uuid.UUID | None = Query(default=None),
    dispositivo_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TelemetriaGps]:
    stmt = select(TelemetriaGps).order_by(TelemetriaGps.timestamp.desc())
    if animal_id is not None:
        stmt = stmt.where(TelemetriaGps.animal_id == animal_id)
    if dispositivo_id is not None:
        stmt = stmt.where(TelemetriaGps.dispositivo_id == dispositivo_id)
    return list(db.scalars(stmt.limit(1000)).all())


# ---------- Geofences ----------

@router.post(
    "/geofences", response_model=GeofenceRead, status_code=status.HTTP_201_CREATED,
)
def criar_geofence(
    payload: GeofenceCreate, db: Session = Depends(get_db),
) -> Geofence:
    g = Geofence(**payload.model_dump())
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.get("/geofences", response_model=list[GeofenceRead])
def listar_geofences(
    fazenda_id: uuid.UUID | None = Query(default=None),
    ativa: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Geofence]:
    stmt = select(Geofence)
    if fazenda_id is not None:
        stmt = stmt.where(Geofence.fazenda_id == fazenda_id)
    if ativa is not None:
        stmt = stmt.where(Geofence.ativa == ativa)
    return list(db.scalars(stmt).all())


@router.patch("/geofences/{gf_id}", response_model=GeofenceRead)
def atualizar_geofence(
    gf_id: uuid.UUID, payload: GeofenceUpdate, db: Session = Depends(get_db),
) -> Geofence:
    g = db.get(Geofence, gf_id)
    if g is None:
        raise HTTPException(status_code=404, detail="geofence nao encontrada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(g, k, v)
    db.commit()
    db.refresh(g)
    return g


@router.delete("/geofences/{gf_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_geofence(gf_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    g = db.get(Geofence, gf_id)
    if g is None:
        raise HTTPException(status_code=404, detail="geofence nao encontrada")
    db.delete(g)
    db.commit()


# ---------- Eventos de geofence ----------

@router.get(
    "/animais/{animal_id}/eventos-geofence",
    response_model=list[EventoGeofenceRead],
)
def listar_eventos_do_animal(
    animal_id: uuid.UUID, db: Session = Depends(get_db),
) -> list[EventoGeofence]:
    stmt = (
        select(EventoGeofence)
        .where(EventoGeofence.animal_id == animal_id)
        .order_by(EventoGeofence.timestamp.desc())
    )
    return list(db.scalars(stmt).all())
