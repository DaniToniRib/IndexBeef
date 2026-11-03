"""Relatorios de acuracia do pipeline vs medicoes de referencia.

GET /relatorio/acuracia?fazenda_id=UUID  — medidas lineares vs manuais
GET /relatorio/pesos?fazenda_id=UUID     — peso estimado vs balanca
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.animal import Animal
from app.models.avaliacao import Avaliacao
from app.models.medida_avaliacao import MedidaAvaliacao
from app.models.pesagem import Pesagem
from app.models.predicao_avaliacao import PredicaoAvaliacao

router = APIRouter(prefix="/relatorio", tags=["relatorio"])

# Par (coluna_pipeline, coluna_manual)
_PARES_MEDIDAS = [
    ("altura_cernelha_cm", "altura_cernelha_manual_cm"),
    ("altura_garupa_cm", "altura_garupa_manual_cm"),
    ("comprimento_corporal_cm", "comprimento_corporal_manual_cm"),
    ("largura_garupa_cm", "largura_garupa_manual_cm"),
    ("perimetro_toracico_est_cm", "perimetro_toracico_manual_cm"),
]


@router.get("/acuracia")
def relatorio_acuracia(
    fazenda_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Compara medidas do pipeline com medicoes manuais de referencia."""

    # Total de avaliacoes (com ou sem medidas manuais)
    stmt_total = select(func.count(Avaliacao.id))
    if fazenda_id is not None:
        stmt_total = stmt_total.join(Animal, Avaliacao.animal_id == Animal.id).where(
            Animal.fazenda_id == fazenda_id,
        )
    total_avaliacoes = db.scalar(stmt_total) or 0

    # Avaliacoes com ao menos uma medida manual preenchida
    stmt_manual = (
        select(func.count(MedidaAvaliacao.id))
        .join(Avaliacao, MedidaAvaliacao.avaliacao_id == Avaliacao.id)
    )
    if fazenda_id is not None:
        stmt_manual = stmt_manual.join(Animal, Avaliacao.animal_id == Animal.id).where(
            Animal.fazenda_id == fazenda_id,
        )
    stmt_manual = stmt_manual.where(
        (MedidaAvaliacao.altura_cernelha_manual_cm.isnot(None))
        | (MedidaAvaliacao.altura_garupa_manual_cm.isnot(None))
        | (MedidaAvaliacao.comprimento_corporal_manual_cm.isnot(None))
        | (MedidaAvaliacao.largura_garupa_manual_cm.isnot(None))
        | (MedidaAvaliacao.perimetro_toracico_manual_cm.isnot(None)),
    )
    com_medidas_manuais = db.scalar(stmt_manual) or 0

    # Metricas por dimensao
    metricas: dict[str, Any] = {}

    stmt_base = (
        select(MedidaAvaliacao)
        .join(Avaliacao, MedidaAvaliacao.avaliacao_id == Avaliacao.id)
    )
    if fazenda_id is not None:
        stmt_base = stmt_base.join(Animal, Avaliacao.animal_id == Animal.id).where(
            Animal.fazenda_id == fazenda_id,
        )

    rows = list(db.scalars(stmt_base).all())

    for col_pipe, col_manual in _PARES_MEDIDAS:
        pares: list[tuple[float, float]] = []
        for m in rows:
            v_pipe = getattr(m, col_pipe)
            v_manual = getattr(m, col_manual)
            if v_pipe is not None and v_manual is not None:
                pares.append((float(v_pipe), float(v_manual)))

        if not pares:
            metricas[col_pipe.replace("_cm", "").replace("_est", "")] = {
                "n": 0,
                "mae_cm": None,
                "mape_pct": None,
                "dentro_3cm_pct": None,
            }
            continue

        n = len(pares)
        erros = [abs(p - r) for p, r in pares]
        mae = sum(erros) / n
        mape = sum(abs(p - r) / r * 100 for p, r in pares if r != 0) / n
        dentro_3 = sum(1 for e in erros if e <= 3.0) / n * 100

        nome = col_pipe.replace("_est_cm", "").replace("_cm", "")
        metricas[nome] = {
            "n": n,
            "mae_cm": round(mae, 2),
            "mape_pct": round(mape, 2),
            "dentro_3cm_pct": round(dentro_3, 1),
        }

    return {
        "total_avaliacoes": total_avaliacoes,
        "com_medidas_manuais": com_medidas_manuais,
        "metricas": metricas,
    }


@router.get("/pesos")
def relatorio_pesos(
    fazenda_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Compara predicao de peso (pipeline) vs pesagem na balanca (mesma data +/- 1 dia)."""
    from sqlalchemy import and_

    # Buscar predicoes de peso_atual
    stmt_pred = (
        select(PredicaoAvaliacao, Avaliacao)
        .join(Avaliacao, PredicaoAvaliacao.avaliacao_id == Avaliacao.id)
        .where(PredicaoAvaliacao.tipo == "peso_atual")
        .where(PredicaoAvaliacao.valor.isnot(None))
    )
    if fazenda_id is not None:
        stmt_pred = stmt_pred.join(Animal, Avaliacao.animal_id == Animal.id).where(
            Animal.fazenda_id == fazenda_id,
        )

    pares: list[tuple[float, float]] = []
    for pred, av in db.execute(stmt_pred).all():
        # Buscar pesagem na balanca do mesmo animal na mesma data
        data_av = av.data_hora.date()
        pesagem = db.scalar(
            select(Pesagem)
            .where(Pesagem.animal_id == av.animal_id)
            .where(Pesagem.origem == "balanca")
            .where(
                and_(
                    Pesagem.data >= data_av,
                    Pesagem.data <= data_av,
                ),
            )
            .limit(1),
        )
        if pesagem is not None and pesagem.peso_kg is not None:
            pares.append((float(pred.valor), float(pesagem.peso_kg)))

    if not pares:
        return {"n_pares": 0, "mape_pct": None, "mae_kg": None, "bias_kg": None, "r2": None}

    n = len(pares)
    reais = [r for _, r in pares]

    mae = sum(abs(p - r) for p, r in pares) / n
    mape = sum(abs(p - r) / r * 100 for p, r in pares if r != 0) / n
    bias = sum(p - r for p, r in pares) / n

    # R²
    media_real = sum(reais) / n
    ss_res = sum((p - r) ** 2 for p, r in pares)
    ss_tot = sum((r - media_real) ** 2 for r in reais)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else None

    return {
        "n_pares": n,
        "mape_pct": round(mape, 2),
        "mae_kg": round(mae, 2),
        "bias_kg": round(bias, 2),
        "r2": round(r2, 4) if r2 is not None else None,
    }
