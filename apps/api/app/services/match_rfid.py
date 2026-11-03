"""Pareamento de leitura RFID -> animal via IdentificacaoEletronica ativa."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identificacao_eletronica import IdentificacaoEletronica


def resolver_animal_por_eid(db: Session, eid: str) -> uuid.UUID | None:
    """Devolve o animal_id do EID se houver IdentificacaoEletronica ativa."""
    stmt = (
        select(IdentificacaoEletronica.animal_id)
        .where(IdentificacaoEletronica.eid == eid)
        .where(IdentificacaoEletronica.ativo.is_(True))
        .limit(1)
    )
    return db.scalar(stmt)
