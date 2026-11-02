"""Schemas Pydantic para o endpoint de avaliacoes.

Entrada: AvaliacaoCreate (keypoints clicados pelo tecnico ja em cm +
metadados do animal). Saida: AvaliacaoRead com status, versao_pipeline e
payload do pipeline (dict JSON produzido por `indexbeef_vision.pipeline`).

Fase 0: processamento sincrono dentro do POST (o pipeline e matematica
pura, roda em ms). Quando houver video e segmentacao, migramos para RQ.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class KeypointCm(BaseModel):
    """Um keypoint em centimetros no plano da placa (apos calibration)."""

    id: int = Field(ge=0, le=17)
    x: float
    y: float


class AvaliacaoCreate(BaseModel):
    """Entrada do POST /avaliacoes.

    Fase 0: o cliente envia os 18 keypoints laterais ja clicados e em cm.
    Em breve o cliente pode mandar frame + ArUco e o worker calibra.
    """

    animal_id: uuid.UUID
    data_hora: datetime
    sexo: Literal["femea", "macho"]
    idade_meses: float = Field(gt=0)
    keypoints_cm: list[KeypointCm] = Field(min_length=18, max_length=18)
    largura_garupa_cm: float | None = Field(default=None, gt=0)
    area_tronco_cm2: float | None = Field(default=None, gt=0)
    largura_torax_cm: float | None = Field(default=None, gt=0)
    observacoes: str | None = None
    avaliador_id: uuid.UUID | None = None


class AvaliacaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    animal_id: uuid.UUID
    data_hora: datetime
    status: str
    versao_pipeline: str | None
    observacoes: str | None
    resultado: dict[str, Any] | None
