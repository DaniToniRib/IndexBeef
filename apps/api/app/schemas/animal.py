from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

SexoStr = Literal["M", "F"]
VariedadeStr = Literal["padrao", "mocho"]
SituacaoStr = Literal["ativo", "vendido", "morto", "descartado"]


class AnimalBase(BaseModel):
    fazenda_id: uuid.UUID
    lote_id: uuid.UUID | None = None
    brinco: str | None = None
    rgn: str | None = None
    rgd: str | None = None
    ceip: bool = False
    rfid: str | None = None
    raca: str = "Nelore"
    variedade: VariedadeStr | None = None
    sexo: SexoStr
    nascimento: date | None = None
    pai_id: uuid.UUID | None = None
    mae_id: uuid.UUID | None = None
    situacao: SituacaoStr = "ativo"
    data_entrada: date | None = None
    observacoes: str | None = None


class AnimalCreate(AnimalBase):
    pass


class AnimalUpdate(BaseModel):
    lote_id: uuid.UUID | None = None
    brinco: str | None = None
    rgn: str | None = None
    rgd: str | None = None
    ceip: bool | None = None
    rfid: str | None = None
    raca: str | None = None
    variedade: VariedadeStr | None = None
    nascimento: date | None = None
    pai_id: uuid.UUID | None = None
    mae_id: uuid.UUID | None = None
    situacao: SituacaoStr | None = None
    data_entrada: date | None = None
    observacoes: str | None = None


class AnimalRead(AnimalBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class PesagemHistorico(BaseModel):
    id: uuid.UUID
    data: date
    peso_kg: Decimal
    origem: str
    gmd_kg_dia: float | None = None  # calculado a partir da pesagem anterior


class AnimalHistorico(BaseModel):
    """Historico consolidado do animal. GMD vem calculado por pesagem."""

    animal_id: uuid.UUID
    pesagens: list[PesagemHistorico]
    gmd_total_kg_dia: float | None = None  # (ultimo - primeiro) / dias
    peso_atual_kg: Decimal | None = None
    idade_dias: int | None = None
    idade_meses: float | None = None
