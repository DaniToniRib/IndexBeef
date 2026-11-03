from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select as sa_select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.animal import Animal
from app.models.avaliacao import Avaliacao
from app.models.dados_geneticos import DadosGeneticos
from app.schemas.animal import (
    AnimalCreate,
    AnimalHistorico,
    AnimalRead,
    AnimalUpdate,
)
from app.schemas.avaliacao import AvaliacaoListItem
from app.schemas.leitura_rfid import ImportacaoResultado
from app.services.csv_animais import parse_csv_animais
from app.services.csv_deps import parse_csv_deps
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
    stmt = sa_select(Animal)
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


@router.get("/{animal_id}/avaliacoes", response_model=list[AvaliacaoListItem])
def listar_avaliacoes_do_animal(
    animal_id: uuid.UUID, db: Session = Depends(get_db),
) -> list[Avaliacao]:
    stmt = (
        sa_select(Avaliacao)
        .where(Avaliacao.animal_id == animal_id)
        .order_by(Avaliacao.data_hora.desc())
    )
    return list(db.scalars(stmt).all())


@router.post("/importar-csv", response_model=ImportacaoResultado)
def importar_csv_animais(
    fazenda_id: uuid.UUID = Query(...),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImportacaoResultado:
    """Importa animais em massa a partir de CSV.

    Colunas minimas: brinco (ou rgn), sexo
    Opcionais: rgn, rgd, nascimento, raca, ceip, variedade, observacoes
    """
    try:
        conteudo = arquivo.file.read().decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=f"arquivo nao e UTF-8: {e}") from e

    linhas, erros = parse_csv_animais(conteudo, fazenda_id)
    if not linhas and erros:
        return ImportacaoResultado(importadas=0, pareadas=0, erros=erros)

    importadas = 0
    for lin in linhas:
        db.add(Animal(**lin))
        importadas += 1
    db.commit()
    return ImportacaoResultado(importadas=importadas, pareadas=importadas, erros=erros)


@router.post("/importar-csv-deps", response_model=ImportacaoResultado)
def importar_csv_deps(
    fazenda_id: uuid.UUID = Query(...),
    arquivo: UploadFile = File(...),
    programa: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ImportacaoResultado:
    """Importa DEPs em massa a partir de CSV (PMGZ/ANCP/Geneplus).

    Colunas de identificacao (ao menos uma): brinco, rgn ou rgd
    Colunas DEP (opcionais): P120, P210, P365, P450, PE, IPP, STAY, PP30, AOL, ACAB, MP120
    Colunas meta (opcionais): programa, safra, indice (ou dti), deca
    """
    try:
        conteudo = arquivo.file.read().decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=f"arquivo nao e UTF-8: {e}") from e

    linhas, erros = parse_csv_deps(conteudo, fazenda_id, programa=programa)
    if not linhas and erros:
        return ImportacaoResultado(importadas=0, pareadas=0, erros=erros)

    importadas = 0
    pareadas = 0
    for lin in linhas:
        # Lookup do animal por brinco/rgn/rgd na fazenda
        animal: Animal | None = None
        for campo in ("brinco", "rgn", "rgd"):
            val = lin.get(campo)
            if val:
                stmt = sa_select(Animal).where(
                    Animal.fazenda_id == fazenda_id,
                    getattr(Animal, campo) == val,
                )
                animal = db.scalars(stmt).first()
                if animal:
                    break

        importadas += 1
        if animal is None:
            ident = lin.get("brinco") or lin.get("rgn") or lin.get("rgd")
            erros.append({
                "linha": str(importadas + 1),
                "motivo": f"animal nao encontrado na fazenda: {ident}",
            })
            continue

        # Upsert DadosGeneticos
        dg = db.scalars(
            sa_select(DadosGeneticos).where(DadosGeneticos.animal_id == animal.id),
        ).first()
        deps_data = {
            "programa": lin.get("programa"),
            "safra": lin.get("safra"),
            "deps": lin.get("deps"),
            "indice_programa": lin.get("indice_programa"),
            "deca": lin.get("deca"),
            "data_importacao": lin.get("data_importacao"),
        }
        if dg is None:
            db.add(DadosGeneticos(animal_id=animal.id, **deps_data))
        else:
            for k, v in deps_data.items():
                setattr(dg, k, v)
        pareadas += 1

    db.commit()
    return ImportacaoResultado(importadas=importadas, pareadas=pareadas, erros=erros)
