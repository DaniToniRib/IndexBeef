"""Calculo de GMD (ganho medio diario) e consolidado do historico do animal."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.animal import Animal
from app.models.pesagem import Pesagem
from app.schemas.animal import AnimalHistorico, PesagemHistorico


def _gmd(p_anterior_kg: Decimal, p_atual_kg: Decimal, dias: int) -> float | None:
    if dias <= 0:
        return None
    return float(p_atual_kg - p_anterior_kg) / dias


def _idade_dias(nascimento: date | None, hoje: date) -> int | None:
    if nascimento is None:
        return None
    return (hoje - nascimento).days


def consolidar_historico(db: Session, animal_id: uuid.UUID) -> AnimalHistorico:
    animal = db.get(Animal, animal_id)
    if animal is None:
        raise ValueError(f"animal nao encontrado: {animal_id}")

    pesagens = list(
        db.scalars(
            select(Pesagem)
            .where(Pesagem.animal_id == animal_id)
            .order_by(Pesagem.data.asc()),
        ).all(),
    )

    pesagens_hist: list[PesagemHistorico] = []
    for i, p in enumerate(pesagens):
        gmd = None
        if i > 0:
            anterior = pesagens[i - 1]
            dias = (p.data - anterior.data).days
            gmd = _gmd(anterior.peso_kg, p.peso_kg, dias)
        pesagens_hist.append(
            PesagemHistorico(
                id=p.id,
                data=p.data,
                peso_kg=p.peso_kg,
                origem=p.origem.value if hasattr(p.origem, "value") else str(p.origem),
                gmd_kg_dia=gmd,
            ),
        )

    gmd_total = None
    peso_atual = None
    if len(pesagens) >= 2:
        dias_totais = (pesagens[-1].data - pesagens[0].data).days
        gmd_total = _gmd(pesagens[0].peso_kg, pesagens[-1].peso_kg, dias_totais)
    if pesagens:
        peso_atual = pesagens[-1].peso_kg

    hoje = date.today()
    idade_dias = _idade_dias(animal.nascimento, hoje)
    idade_meses = idade_dias / 30.4375 if idade_dias is not None else None

    return AnimalHistorico(
        animal_id=animal.id,
        pesagens=pesagens_hist,
        gmd_total_kg_dia=gmd_total,
        peso_atual_kg=peso_atual,
        idade_dias=idade_dias,
        idade_meses=idade_meses,
    )
