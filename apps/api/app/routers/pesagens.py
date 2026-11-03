from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.animal import Animal
from app.models.identificacao_eletronica import IdentificacaoEletronica
from app.models.pesagem import Pesagem
from app.schemas.leitura_rfid import ImportacaoResultado
from app.schemas.pesagem import PesagemCreate, PesagemRead
from app.services.csv_bastao import parse_csv_balanca
from app.services.match_rfid import resolver_animal_por_eid

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


def _match_animal(db: Session, eid: str | None, vid: str | None) -> uuid.UUID | None:
    if eid:
        aid = resolver_animal_por_eid(db, eid)
        if aid:
            return aid
    if vid:
        # Match por VID (brinco visual) na tabela Animal ou IdentificacaoEletronica.
        aid = db.scalar(select(Animal.id).where(Animal.brinco == vid))
        if aid:
            return aid
        aid = db.scalar(
            select(IdentificacaoEletronica.animal_id)
            .where(IdentificacaoEletronica.vid == vid)
            .where(IdentificacaoEletronica.ativo.is_(True)),
        )
        if aid:
            return aid
    return None


@router.post("/importar-csv", response_model=ImportacaoResultado)
def importar_csv_balanca(
    arquivo: UploadFile = File(...),
    dispositivo_id: uuid.UUID | None = Query(default=None),
    origem: str = Query(default="balanca"),
    db: Session = Depends(get_db),
) -> ImportacaoResultado:
    try:
        conteudo = arquivo.file.read().decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=f"arquivo nao e UTF-8: {e}") from e

    linhas, erros = parse_csv_balanca(conteudo)
    if not linhas and erros:
        return ImportacaoResultado(importadas=0, pareadas=0, erros=erros)

    importadas = 0
    pareadas = 0
    for i, lin in enumerate(linhas, start=2):
        animal_id = _match_animal(db, lin.get("eid"), lin.get("vid"))
        if animal_id is None:
            erros.append(
                {
                    "linha": str(i),
                    "motivo": f"nenhum animal pareado (eid={lin.get('eid')!r}, "
                              f"vid={lin.get('vid')!r})",
                },
            )
            continue
        db.add(
            Pesagem(
                animal_id=animal_id,
                data=lin["data"],
                peso_kg=lin["peso_kg"],
                origem=origem,
                dispositivo_id=dispositivo_id,
            ),
        )
        importadas += 1
        pareadas += 1
    db.commit()
    return ImportacaoResultado(importadas=importadas, pareadas=pareadas, erros=erros)
