"""Router de modelo_versao — registro e ativacao de modelos ML treinados."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.modelo_versao import ModeloVersao
from app.schemas.modelo_versao import ModeloVersaoCreate, ModeloVersaoRead

router = APIRouter(prefix="/modelos-versao", tags=["modelos-versao"])


@router.post("", response_model=ModeloVersaoRead, status_code=status.HTTP_201_CREATED)
def criar_modelo_versao(
    payload: ModeloVersaoCreate,
    db: Session = Depends(get_db),
) -> ModeloVersao:
    modelo = ModeloVersao(
        nome=payload.nome,
        versao=payload.versao,
        metricas=payload.metricas,
        artefato_url=payload.artefato_url,
        ativo=payload.ativo,
        descricao=payload.descricao,
    )
    db.add(modelo)
    db.commit()
    db.refresh(modelo)
    return modelo


@router.get("", response_model=list[ModeloVersaoRead])
def listar_modelos_versao(
    nome: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[ModeloVersao]:
    stmt = select(ModeloVersao).order_by(ModeloVersao.criado_em.desc())
    if nome is not None:
        stmt = stmt.where(ModeloVersao.nome == nome)
    return list(db.scalars(stmt).all())


@router.get("/{modelo_id}", response_model=ModeloVersaoRead)
def ler_modelo_versao(
    modelo_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ModeloVersao:
    modelo = db.get(ModeloVersao, modelo_id)
    if modelo is None:
        raise HTTPException(status_code=404, detail="modelo_versao nao encontrado")
    return modelo


@router.patch("/{modelo_id}/ativar", response_model=ModeloVersaoRead)
def ativar_modelo_versao(
    modelo_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ModeloVersao:
    """Ativa este modelo e desativa todos os outros com o mesmo nome."""
    modelo = db.get(ModeloVersao, modelo_id)
    if modelo is None:
        raise HTTPException(status_code=404, detail="modelo_versao nao encontrado")

    # Desativar todos do mesmo nome
    db.execute(
        update(ModeloVersao)
        .where(ModeloVersao.nome == modelo.nome)
        .values(ativo=False),
    )
    # Ativar este
    modelo.ativo = True
    db.commit()
    db.refresh(modelo)
    return modelo
