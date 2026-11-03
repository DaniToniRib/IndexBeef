from __future__ import annotations

import re
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TipoAplicacaoStr = Literal["vacina", "vermifugo", "terapeutico"]
ViaStr = Literal["IM", "SC", "IV", "oral", "topico", "outra"]

# CRMV padrao: "UF-NNNNN" ou "UF NNNNN". A validacao e leve (nao chama API do CFMV).
_RE_CRMV = re.compile(r"^[A-Za-z]{2}[-\s]?\d{3,7}$")


class AplicacaoSanitariaBase(BaseModel):
    animal_id: uuid.UUID
    campanha_id: uuid.UUID | None = None
    tipo: TipoAplicacaoStr
    data: date
    principio_ativo: str
    nome_comercial: str | None = None
    concentracao: str | None = None
    dose_ml: Decimal | None = Field(default=None, gt=0)
    dose_mg_por_kg: Decimal | None = Field(default=None, gt=0)
    via: ViaStr
    lote_medicamento: str | None = None
    validade: date | None = None
    carencia_abate_dias: int | None = Field(default=None, ge=0)
    carencia_leite_dias: int | None = Field(default=None, ge=0)
    veterinario_crmv: str | None = None
    veterinario_nome: str | None = None
    receita_url: str | None = None
    observacoes: str | None = None

    @model_validator(mode="after")
    def valida_regras(self) -> AplicacaoSanitariaBase:
        # Vacina e terapeutico exigem CRMV (ver docs/11 §4 e §5).
        if self.tipo in ("vacina", "terapeutico") and not self.veterinario_crmv:
            raise ValueError(
                f"veterinario_crmv e obrigatorio para tipo={self.tipo} "
                f"(ver docs/11 §4 / Res. CFMV 1138/2016)",
            )
        if self.veterinario_crmv and not _RE_CRMV.match(self.veterinario_crmv):
            raise ValueError(
                f"veterinario_crmv invalido: {self.veterinario_crmv!r} "
                "(formato esperado: 'UF-NNNNN', ex: 'SP-12345')",
            )
        if self.validade is not None and self.validade < self.data:
            raise ValueError(
                f"medicamento vencido na data da aplicacao "
                f"(validade={self.validade}, aplicacao={self.data})",
            )
        return self


class AplicacaoSanitariaCreate(AplicacaoSanitariaBase):
    pass


class AplicacaoSanitariaRead(AplicacaoSanitariaBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    apto_abate_em: date | None = None
    apto_consumo_leite_em: date | None = None

    @classmethod
    def from_model(cls, obj) -> AplicacaoSanitariaRead:
        apto_abate = (
            obj.data + timedelta(days=obj.carencia_abate_dias)
            if obj.carencia_abate_dias is not None
            else None
        )
        apto_leite = (
            obj.data + timedelta(days=obj.carencia_leite_dias)
            if obj.carencia_leite_dias is not None
            else None
        )
        return cls.model_validate(
            {
                **{k: getattr(obj, k) for k in AplicacaoSanitariaBase.model_fields},
                "id": obj.id,
                "apto_abate_em": apto_abate,
                "apto_consumo_leite_em": apto_leite,
            },
        )
