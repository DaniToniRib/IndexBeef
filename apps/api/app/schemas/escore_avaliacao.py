"""Schemas Pydantic para ECC e EPMURAS."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EscoreInput(BaseModel):
    """Notas do tecnico coletadas em campo (antes do processamento)."""

    ecc: float | None = None  # Escore de Condicao Corporal (1-9)
    e: int | None = None  # Estrutura
    p: int | None = None  # Precocidade
    m: int | None = None  # Musculosidade
    u: int | None = None  # Umbigo
    r: int | None = None  # Racial
    a: int | None = None  # Aprumos
    s: int | None = None  # Sexualidade


class EscoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ecc_final: float | None = None
    frame_score: float | None = None
    e_final: int | None = None
    p_final: int | None = None
    m_final: int | None = None
    u_final: int | None = None
    r_final: int | None = None
    a_final: int | None = None
    s_final: int | None = None
