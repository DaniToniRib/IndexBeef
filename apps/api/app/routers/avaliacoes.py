"""Router de avaliacoes.

POST /avaliacoes: enfileira task RQ para processar pipeline em segundo plano.
  - Fallback sincrono quando Redis nao esta disponivel (testes / dev offline).
GET /avaliacoes/{id}: retorna avaliacao com tabelas estruturadas.
GET /avaliacoes?animal_id=: lista avaliacoes de um animal.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from indexbeef_vision.pipeline import VERSAO_PIPELINE, montar_payload
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.redis_queue import get_queue
from app.models.avaliacao import Avaliacao
from app.models.enums import StatusAvaliacao
from app.models.escore_avaliacao import EscoreAvaliacao
from app.models.medida_avaliacao import MedidaAvaliacao
from app.schemas.avaliacao import AvaliacaoCreate, AvaliacaoListItem, AvaliacaoRead
from app.services.resultado_service import salvar_resultado_estruturado

router = APIRouter(prefix="/avaliacoes", tags=["avaliacoes"])


def _kp_dict(payload: AvaliacaoCreate) -> dict[int, tuple[float, float]]:
    return {kp.id: (kp.x, kp.y) for kp in payload.keypoints_cm}


@router.post("", response_model=AvaliacaoRead, status_code=status.HTTP_201_CREATED)
def criar_avaliacao(payload: AvaliacaoCreate, db: Session = Depends(get_db)) -> Avaliacao:
    kp_cm = _kp_dict(payload)
    if set(kp_cm.keys()) != set(range(18)):
        raise HTTPException(
            status_code=400,
            detail="keypoints_cm deve conter exatamente os IDs 0..17 (sem repeticao).",
        )

    params: dict = {
        "kp_cm": {str(k): list(v) for k, v in kp_cm.items()},
        "sexo": payload.sexo,
        "idade_meses": payload.idade_meses,
        "largura_garupa_cm": payload.largura_garupa_cm,
        "area_tronco_cm2": payload.area_tronco_cm2,
        "largura_torax_cm": payload.largura_torax_cm,
    }

    avaliacao = Avaliacao(
        animal_id=payload.animal_id,
        data_hora=payload.data_hora,
        avaliador_id=payload.avaliador_id,
        observacoes=payload.observacoes,
        status=StatusAvaliacao.processando,
        parametros_entrada=params,
    )
    db.add(avaliacao)
    db.flush()

    fila = get_queue()
    if fila is not None:
        # Pre-criar MedidaAvaliacao com medidas manuais para que o ON CONFLICT do worker
        # nao as sobrescreva (o worker so faz UPDATE SET nas colunas do pipeline)
        if payload.medidas_manuais is not None:
            mm = payload.medidas_manuais
            db.add(MedidaAvaliacao(
                avaliacao_id=avaliacao.id,
                altura_cernelha_manual_cm=mm.altura_cernelha_cm,
                altura_garupa_manual_cm=mm.altura_garupa_cm,
                comprimento_corporal_manual_cm=mm.comprimento_corporal_cm,
                largura_garupa_manual_cm=mm.largura_garupa_cm,
                perimetro_toracico_manual_cm=mm.perimetro_toracico_cm,
            ))
        if payload.escore is not None:
            e = payload.escore
            db.add(EscoreAvaliacao(
                avaliacao_id=avaliacao.id,
                ecc_final=e.ecc,
                e_final=e.e,
                p_final=e.p,
                m_final=e.m,
                u_final=e.u,
                r_final=e.r,
                a_final=e.a,
                s_final=e.s,
            ))
        fila.enqueue(
            "indexbeef_worker.tasks.processar_avaliacao",
            str(avaliacao.id),
            job_timeout=120,
        )
        db.commit()
        db.refresh(avaliacao)
        return avaliacao

    # Fallback sincrono (Redis indisponivel)
    try:
        resultado = montar_payload(
            avaliacao_id=avaliacao.id,
            kp_cm=kp_cm,
            sexo=payload.sexo,
            idade_meses=payload.idade_meses,
            largura_garupa_cm=payload.largura_garupa_cm,
            area_tronco_cm2=payload.area_tronco_cm2,
            largura_torax_cm=payload.largura_torax_cm,
        )
    except Exception as e:
        avaliacao.status = StatusAvaliacao.erro
        avaliacao.observacoes = f"erro no pipeline: {e!s}"
        db.commit()
        raise HTTPException(status_code=422, detail=f"pipeline falhou: {e!s}") from e

    avaliacao.resultado = resultado
    avaliacao.versao_pipeline = VERSAO_PIPELINE
    avaliacao.status = StatusAvaliacao.concluida
    mm_dict = payload.medidas_manuais.model_dump() if payload.medidas_manuais else None
    salvar_resultado_estruturado(db, avaliacao, resultado, mm_dict)
    if payload.escore is not None:
        e = payload.escore
        db.add(EscoreAvaliacao(
            avaliacao_id=avaliacao.id,
            ecc_final=e.ecc,
            e_final=e.e,
            p_final=e.p,
            m_final=e.m,
            u_final=e.u,
            r_final=e.r,
            a_final=e.a,
            s_final=e.s,
        ))
    db.commit()
    db.refresh(avaliacao)
    return avaliacao


@router.get("", response_model=list[AvaliacaoListItem])
def listar_avaliacoes(
    animal_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> list[Avaliacao]:
    stmt = (
        select(Avaliacao)
        .where(Avaliacao.animal_id == animal_id)
        .order_by(Avaliacao.data_hora.desc())
    )
    return list(db.scalars(stmt).all())


@router.get("/{avaliacao_id}", response_model=AvaliacaoRead)
def ler_avaliacao(avaliacao_id: uuid.UUID, db: Session = Depends(get_db)) -> Avaliacao:
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status_code=404, detail="avaliacao nao encontrada")
    return avaliacao


@router.get("/{avaliacao_id}/reprocessar", response_model=AvaliacaoRead)
def reprocessar_avaliacao(
    avaliacao_id: uuid.UUID, db: Session = Depends(get_db),
) -> Avaliacao:
    """Re-enfileira (ou re-executa sync) uma avaliacao ja criada."""
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status_code=404, detail="avaliacao nao encontrada")
    if avaliacao.parametros_entrada is None:
        raise HTTPException(status_code=422, detail="avaliacao sem parametros_entrada")

    avaliacao.status = StatusAvaliacao.processando
    avaliacao.resultado = None
    db.commit()

    fila = get_queue()
    if fila is not None:
        fila.enqueue(
            "indexbeef_worker.tasks.processar_avaliacao",
            str(avaliacao.id),
            job_timeout=120,
        )
        db.refresh(avaliacao)
        return avaliacao

    p = avaliacao.parametros_entrada
    kp_cm = {int(k): tuple(v) for k, v in p["kp_cm"].items()}
    try:
        resultado = montar_payload(
            avaliacao_id=avaliacao.id,
            kp_cm=kp_cm,
            sexo=p["sexo"],
            idade_meses=p["idade_meses"],
            largura_garupa_cm=p.get("largura_garupa_cm"),
            area_tronco_cm2=p.get("area_tronco_cm2"),
            largura_torax_cm=p.get("largura_torax_cm"),
        )
    except Exception as e:
        avaliacao.status = StatusAvaliacao.erro
        db.commit()
        raise HTTPException(status_code=422, detail=f"pipeline falhou: {e!s}") from e

    avaliacao.resultado = resultado
    avaliacao.versao_pipeline = VERSAO_PIPELINE
    avaliacao.status = StatusAvaliacao.concluida
    salvar_resultado_estruturado(db, avaliacao, resultado)
    db.commit()
    db.refresh(avaliacao)
    return avaliacao
