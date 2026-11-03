from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import TipoAplicacaoSanitaria, ViaAdministracao

if TYPE_CHECKING:
    from app.models.animal import Animal
    from app.models.campanha import Campanha


class AplicacaoSanitaria(SyncMixin, Base):
    """Aplicacao sanitaria individual em um animal (vacina/vermifugo/terapeutico).

    Campos obrigatorios por tipo seguem Res. CFMV 1138/2016 (ver docs/11 §5).
    `apto_abate_em` e calculado em schema/service: data + carencia_abate_dias.
    """

    __tablename__ = "aplicacao_sanitaria"

    animal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False,
    )
    campanha_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("campanha.id", ondelete="SET NULL"), nullable=True,
    )
    tipo: Mapped[TipoAplicacaoSanitaria] = mapped_column(
        SAEnum(TipoAplicacaoSanitaria, name="tipo_aplicacao_sanitaria"),
        nullable=False,
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)

    principio_ativo: Mapped[str] = mapped_column(String, nullable=False)
    nome_comercial: Mapped[str | None] = mapped_column(String, nullable=True)
    concentracao: Mapped[str | None] = mapped_column(String, nullable=True)
    dose_ml: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    dose_mg_por_kg: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    via: Mapped[ViaAdministracao] = mapped_column(
        SAEnum(ViaAdministracao, name="via_administracao"), nullable=False,
    )

    lote_medicamento: Mapped[str | None] = mapped_column(String, nullable=True)
    validade: Mapped[date | None] = mapped_column(Date, nullable=True)

    carencia_abate_dias: Mapped[int | None] = mapped_column(nullable=True)
    carencia_leite_dias: Mapped[int | None] = mapped_column(nullable=True)

    # Veterinario responsavel — obrigatorio para vacina (brucelose B19 so com
    # vet habilitado MAPA) e para terapeutico (prescricao CFMV); opcional para
    # vermifugo rotineiro de rebanho (feito pelo proprio produtor).
    veterinario_crmv: Mapped[str | None] = mapped_column(String, nullable=True)
    veterinario_nome: Mapped[str | None] = mapped_column(String, nullable=True)

    receita_url: Mapped[str | None] = mapped_column(String, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    animal: Mapped[Animal] = relationship()
    campanha: Mapped[Campanha | None] = relationship(back_populates="aplicacoes")
