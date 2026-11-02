"""Router de avaliacoes.

POST /avaliacoes recebe os 18 keypoints em cm, roda o pipeline da Fase 0
(indexbeef_vision) sincronamente e persiste status + resultado.
GET /avaliacoes/{id} devolve o registro com o payload do pipeline.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from indexbeef_vision.pipeline import VERSAO_PIPELINE, montar_payload
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.avaliacao import Avaliacao
from app.models.enums import StatusAvaliacao
from app.schemas.avaliacao import AvaliacaoCreate, AvaliacaoRead

router = APIRouter(prefix="/avaliacoes", tags=["avaliacoes"])


@router.post("", response_model=AvaliacaoRead, status_code=status.HTTP_201_CREATED)
def criar_avaliacao(payload: AvaliacaoCreate, db: Session = Depends(get_db)) -> Avaliacao:
    kp_cm = {kp.id: (kp.x, kp.y) for kp in payload.keypoints_cm}
    if set(kp_cm.keys()) != set(range(18)):
        raise HTTPException(
            status_code=400,
            detail="keypoints_cm deve conter exatamente os IDs 0..17 (sem repeticao).",
        )

    avaliacao = Avaliacao(
        animal_id=payload.animal_id,
        data_hora=payload.data_hora,
        avaliador_id=payload.avaliador_id,
        observacoes=payload.observacoes,
        status=StatusAvaliacao.processando,
    )
    db.add(avaliacao)
    db.flush()

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
    db.commit()
    db.refresh(avaliacao)
    return avaliacao


@router.get("/{avaliacao_id}", response_model=AvaliacaoRead)
def ler_avaliacao(avaliacao_id: uuid.UUID, db: Session = Depends(get_db)) -> Avaliacao:
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status_code=404, detail="avaliacao nao encontrada")
    return avaliacao
