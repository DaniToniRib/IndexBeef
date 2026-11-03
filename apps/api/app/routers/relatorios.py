"""Endpoint de relatorios PDF."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.animal import Animal
from app.models.aplicacao_sanitaria import AplicacaoSanitaria
from app.models.atendimento_veterinario import AtendimentoVeterinario
from app.models.avaliacao import Avaliacao
from app.schemas.animal import AnimalRead
from app.schemas.avaliacao import AvaliacaoRead
from app.services.historico import consolidar_historico
from app.services.relatorio_service import gerar_relatorio_animal

router = APIRouter(prefix="/animais", tags=["relatorios"])


@router.get("/{animal_id}/relatorio")
def relatorio_animal(animal_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    """Retorna PDF com ficha completa do animal."""
    animal = db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="animal nao encontrado")

    try:
        historico = consolidar_historico(db, animal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    aplicacoes = list(db.scalars(
        select(AplicacaoSanitaria)
        .where(AplicacaoSanitaria.animal_id == animal_id)
        .order_by(AplicacaoSanitaria.data.desc()),
    ).all())

    atendimentos = list(db.scalars(
        select(AtendimentoVeterinario)
        .where(AtendimentoVeterinario.animal_id == animal_id)
        .order_by(AtendimentoVeterinario.data_hora.desc()),
    ).all())

    avaliacoes_orm = list(db.scalars(
        select(Avaliacao)
        .where(Avaliacao.animal_id == animal_id)
        .order_by(Avaliacao.data_hora.desc()),
    ).all())

    def _model_to_dict(obj) -> dict:
        schema_cls = AvaliacaoRead
        return schema_cls.model_validate(obj).model_dump()

    animal_dict = AnimalRead.model_validate(animal).model_dump()
    historico_dict = historico.model_dump()
    aplicacoes_dicts = [a.__dict__ for a in aplicacoes]
    atendimentos_dicts = [a.__dict__ for a in atendimentos]
    avaliacoes_dicts = [_model_to_dict(av) for av in avaliacoes_orm]

    try:
        pdf_bytes = gerar_relatorio_animal(
            animal=animal_dict,
            historico=historico_dict,
            aplicacoes=aplicacoes_dicts,
            atendimentos=atendimentos_dicts,
            avaliacoes=avaliacoes_dicts,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"erro ao gerar PDF: {e!s}") from e

    brinco = animal.brinco or str(animal_id)[:8]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ficha-{brinco}.pdf"'},
    )
