"""Schemas Pydantic para o endpoint de avaliacoes."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.captura import CapturaRead
from app.schemas.escore_avaliacao import EscoreInput, EscoreRead


class KeypointCm(BaseModel):
    id: int = Field(ge=0, le=17)
    x: float
    y: float


class MedidasManuaisInput(BaseModel):
    """Medidas de referencia coletadas com instrumentos fisicos (subconjunto ~1:3 dos animais)."""

    altura_cernelha_cm: float | None = None
    altura_garupa_cm: float | None = None
    comprimento_corporal_cm: float | None = None
    largura_garupa_cm: float | None = None
    perimetro_toracico_cm: float | None = None


class AvaliacaoCreate(BaseModel):
    animal_id: uuid.UUID
    data_hora: datetime
    sexo: Literal["femea", "macho"]
    idade_meses: float = Field(gt=0)
    keypoints_cm: list[KeypointCm] = Field(min_length=18, max_length=18)
    largura_garupa_cm: float | None = Field(default=None, gt=0)
    area_tronco_cm2: float | None = Field(default=None, gt=0)
    largura_torax_cm: float | None = Field(default=None, gt=0)
    px_por_cm: float | None = None  # escala usada na captura (pixels por cm)
    observacoes: str | None = None
    avaliador_id: uuid.UUID | None = None
    # Notas do tecnico (campo)
    escore: EscoreInput | None = None
    medidas_manuais: MedidasManuaisInput | None = None


# --- Schemas de leitura para tabelas estruturadas ---

class MedidasRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    altura_cernelha_cm: Decimal | None = None
    altura_cernelha_conf: Decimal | None = None
    altura_garupa_cm: Decimal | None = None
    altura_garupa_conf: Decimal | None = None
    comprimento_corporal_cm: Decimal | None = None
    comprimento_corporal_conf: Decimal | None = None
    profundidade_toracica_cm: Decimal | None = None
    profundidade_toracica_conf: Decimal | None = None
    comprimento_garupa_cm: Decimal | None = None
    comprimento_garupa_conf: Decimal | None = None
    largura_garupa_cm: Decimal | None = None
    largura_garupa_conf: Decimal | None = None
    altura_cupim_cm: Decimal | None = None
    altura_cupim_conf: Decimal | None = None
    umbigo_chao_cm: Decimal | None = None
    umbigo_chao_conf: Decimal | None = None
    perimetro_toracico_est_cm: Decimal | None = None
    perimetro_toracico_est_conf: Decimal | None = None
    inclinacao_garupa_graus: Decimal | None = None
    jarrete_graus: Decimal | None = None


class CaixaVirtualRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    c_cm: Decimal | None = None
    p_cm: Decimal | None = None
    l_cm: Decimal | None = None
    volume_cm3: Decimal | None = None
    volume_l: Decimal | None = None
    ipl: Decimal | None = None
    compacidade: Decimal | None = None
    indice_comprimento: Decimal | None = None


class PredicaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo: str
    valor: Decimal | None = None
    faixa_min: Decimal | None = None
    faixa_max: Decimal | None = None
    confianca: Decimal | None = None
    metodo: str | None = None


class AvaliacaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    animal_id: uuid.UUID
    data_hora: datetime
    status: str
    versao_pipeline: str | None
    observacoes: str | None
    resultado: dict[str, Any] | None
    # Tabelas estruturadas (populadas apos processamento)
    medida: MedidasRead | None = None
    caixa_virtual: CaixaVirtualRead | None = None
    predicoes: list[PredicaoRead] = []
    capturas: list[CapturaRead] = []
    escore: EscoreRead | None = None


class AvaliacaoListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    data_hora: datetime
    status: str
    versao_pipeline: str | None
    observacoes: str | None
