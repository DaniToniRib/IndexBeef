from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.leitura_rfid import LeituraRfid
from app.schemas.leitura_rfid import (
    ImportacaoResultado,
    LeituraRfidBatchCreate,
    LeituraRfidCreate,
    LeituraRfidRead,
)
from app.services.csv_bastao import parse_csv_bastao
from app.services.match_rfid import resolver_animal_por_eid

router = APIRouter(prefix="/leituras/rfid", tags=["leituras-rfid"])


def _persistir_lote(
    db: Session, leituras: list[LeituraRfidCreate],
) -> tuple[list[LeituraRfid], int]:
    pareadas = 0
    objs: list[LeituraRfid] = []
    agora = datetime.now(UTC)
    for lei in leituras:
        animal_id = resolver_animal_por_eid(db, lei.eid)
        obj = LeituraRfid(
            **lei.model_dump(),
            animal_id=animal_id,
            pareado_em=agora if animal_id else None,
        )
        db.add(obj)
        objs.append(obj)
        if animal_id:
            pareadas += 1
    db.commit()
    for o in objs:
        db.refresh(o)
    return objs, pareadas


@router.post("", response_model=list[LeituraRfidRead], status_code=status.HTTP_201_CREATED)
def ingerir_lote(
    payload: LeituraRfidBatchCreate, db: Session = Depends(get_db),
) -> list[LeituraRfid]:
    objs, _ = _persistir_lote(db, payload.leituras)
    return objs


@router.post("/importar-csv", response_model=ImportacaoResultado)
def importar_csv(
    arquivo: UploadFile = File(...),
    dispositivo_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ImportacaoResultado:
    try:
        conteudo = arquivo.file.read().decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=f"arquivo nao e UTF-8: {e}") from e

    leituras, erros = parse_csv_bastao(conteudo, dispositivo_id=dispositivo_id)
    if not leituras and erros:
        return ImportacaoResultado(importadas=0, pareadas=0, erros=erros)

    _, pareadas = _persistir_lote(db, leituras)
    return ImportacaoResultado(
        importadas=len(leituras), pareadas=pareadas, erros=erros,
    )


@router.get("", response_model=list[LeituraRfidRead])
def listar(
    eid: str | None = Query(default=None),
    animal_id: uuid.UUID | None = Query(default=None),
    pareado: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[LeituraRfid]:
    stmt = select(LeituraRfid).order_by(LeituraRfid.timestamp.desc())
    if eid is not None:
        stmt = stmt.where(LeituraRfid.eid == eid)
    if animal_id is not None:
        stmt = stmt.where(LeituraRfid.animal_id == animal_id)
    if pareado is True:
        stmt = stmt.where(LeituraRfid.animal_id.is_not(None))
    elif pareado is False:
        stmt = stmt.where(LeituraRfid.animal_id.is_(None))
    return list(db.scalars(stmt).all())
