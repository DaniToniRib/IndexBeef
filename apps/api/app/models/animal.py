from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin
from app.models.enums import Sexo, SituacaoAnimal, Variedade

if TYPE_CHECKING:
    from app.models.avaliacao import Avaliacao
    from app.models.dados_geneticos import DadosGeneticos
    from app.models.evento_reprodutivo import EventoReprodutivo
    from app.models.exame_andrologico import ExameAndrologico
    from app.models.identificacao_eletronica import IdentificacaoEletronica
    from app.models.lote import Lote
    from app.models.pesagem import Pesagem


class Animal(SyncMixin, Base):
    __tablename__ = "animal"

    fazenda_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False,
    )
    lote_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("lote.id", ondelete="SET NULL"), nullable=True,
    )

    brinco: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    rgn: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    rgd: Mapped[str | None] = mapped_column(String, nullable=True)
    ceip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rfid: Mapped[str | None] = mapped_column(String, nullable=True)
    raca: Mapped[str] = mapped_column(String, nullable=False, default="Nelore")
    variedade: Mapped[Variedade | None] = mapped_column(
        SAEnum(Variedade, name="variedade"), nullable=True,
    )
    sexo: Mapped[Sexo] = mapped_column(SAEnum(Sexo, name="sexo"), nullable=False)
    nascimento: Mapped[date | None] = mapped_column(Date, nullable=True)

    pai_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="SET NULL"), nullable=True,
    )
    mae_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("animal.id", ondelete="SET NULL"), nullable=True,
    )

    situacao: Mapped[SituacaoAnimal] = mapped_column(
        SAEnum(SituacaoAnimal, name="situacao_animal"),
        nullable=False,
        default=SituacaoAnimal.ativo,
    )

    data_entrada: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    lote: Mapped[Lote | None] = relationship(back_populates="animais")
    pesagens: Mapped[list[Pesagem]] = relationship(
        back_populates="animal", cascade="all, delete-orphan",
    )
    avaliacoes: Mapped[list[Avaliacao]] = relationship(
        back_populates="animal", cascade="all, delete-orphan",
    )
    identificacoes_eletronicas: Mapped[list[IdentificacaoEletronica]] = relationship(
        back_populates="animal", cascade="all, delete-orphan",
    )

    pai: Mapped[Animal | None] = relationship(
        "Animal", remote_side="Animal.id", foreign_keys=[pai_id],
    )
    mae: Mapped[Animal | None] = relationship(
        "Animal", remote_side="Animal.id", foreign_keys=[mae_id],
    )

    dados_geneticos: Mapped[DadosGeneticos | None] = relationship(
        back_populates="animal", cascade="all, delete-orphan", uselist=False,
    )
    eventos_reprodutivos: Mapped[list[EventoReprodutivo]] = relationship(
        foreign_keys="EventoReprodutivo.animal_id",
        back_populates="animal",
        cascade="all, delete-orphan",
    )
    exames_andrologicos: Mapped[list[ExameAndrologico]] = relationship(
        back_populates="animal", cascade="all, delete-orphan",
    )
