"""inicial: fazenda, lote, animal, pesagem, avaliacao, captura

Revision ID: 0001_inicial
Revises:
Create Date: 2026-11-02 00:00:00

Primeira migracao do IndexBeef. Cria as 6 tabelas de dominio do docs/06
(fazenda, lote, animal, pesagem, avaliacao, captura) com os campos
obrigatorios do SyncMixin (id UUID, criado_em, atualizado_em,
origem_estacao, sincronizado_em).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_inicial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _sync_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("origem_estacao", sa.String(), nullable=True),
        sa.Column("sincronizado_em", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    # Enums sao criados explicitamente antes das tabelas; depois usamos
    # `create_type=False` para o op.create_table nao tentar recriar o tipo.
    categoria_lote = sa.Enum(
        "bezerro", "garrote", "novilha", "matriz", "touro", name="categoria_lote",
    )
    variedade = sa.Enum("padrao", "mocho", name="variedade")
    sexo = sa.Enum("M", "F", name="sexo")
    situacao_animal = sa.Enum(
        "ativo", "vendido", "morto", "descartado", name="situacao_animal",
    )
    status_avaliacao = sa.Enum(
        "capturada",
        "processando",
        "revisar",
        "concluida",
        "erro",
        name="status_avaliacao",
    )
    origem_pesagem = sa.Enum("balanca", "estimado", "fita", name="origem_pesagem")
    tipo_captura = sa.Enum("ao_vivo", "video", "foto", name="tipo_captura")
    vista_captura = sa.Enum(
        "lateral", "traseira", "dorsal", "frontal", name="vista_captura",
    )
    bind = op.get_bind()
    for enum_type in (
        categoria_lote,
        variedade,
        sexo,
        situacao_animal,
        status_avaliacao,
        origem_pesagem,
        tipo_captura,
        vista_captura,
    ):
        enum_type.create(bind, checkfirst=True)

    categoria_lote_ref = sa.Enum(
        "bezerro",
        "garrote",
        "novilha",
        "matriz",
        "touro",
        name="categoria_lote",
        create_type=False,
    )
    variedade_ref = sa.Enum("padrao", "mocho", name="variedade", create_type=False)
    sexo_ref = sa.Enum("M", "F", name="sexo", create_type=False)
    situacao_animal_ref = sa.Enum(
        "ativo",
        "vendido",
        "morto",
        "descartado",
        name="situacao_animal",
        create_type=False,
    )
    status_avaliacao_ref = sa.Enum(
        "capturada",
        "processando",
        "revisar",
        "concluida",
        "erro",
        name="status_avaliacao",
        create_type=False,
    )
    origem_pesagem_ref = sa.Enum(
        "balanca", "estimado", "fita", name="origem_pesagem", create_type=False,
    )
    tipo_captura_ref = sa.Enum(
        "ao_vivo", "video", "foto", name="tipo_captura", create_type=False,
    )
    vista_captura_ref = sa.Enum(
        "lateral",
        "traseira",
        "dorsal",
        "frontal",
        name="vista_captura",
        create_type=False,
    )

    op.create_table(
        "fazenda",
        *_sync_columns(),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("municipio", sa.String(), nullable=True),
        sa.Column("uf", sa.String(length=2), nullable=True),
        sa.Column("bioma", sa.String(), nullable=True),
    )

    op.create_table(
        "lote",
        *_sync_columns(),
        sa.Column(
            "fazenda_id",
            sa.Uuid(),
            sa.ForeignKey("fazenda.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("categoria", categoria_lote_ref, nullable=False),
    )

    op.create_table(
        "animal",
        *_sync_columns(),
        sa.Column(
            "fazenda_id",
            sa.Uuid(),
            sa.ForeignKey("fazenda.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lote_id",
            sa.Uuid(),
            sa.ForeignKey("lote.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("brinco", sa.String(), nullable=True),
        sa.Column("rgn", sa.String(), nullable=True),
        sa.Column("rgd", sa.String(), nullable=True),
        sa.Column(
            "ceip",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("rfid", sa.String(), nullable=True),
        sa.Column(
            "raca",
            sa.String(),
            nullable=False,
            server_default=sa.text("'Nelore'"),
        ),
        sa.Column("variedade", variedade_ref, nullable=True),
        sa.Column("sexo", sexo_ref, nullable=False),
        sa.Column("nascimento", sa.Date(), nullable=True),
        sa.Column(
            "pai_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "mae_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "situacao",
            situacao_animal_ref,
            nullable=False,
            server_default=sa.text("'ativo'"),
        ),
    )
    op.create_index("ix_animal_brinco", "animal", ["brinco"])
    op.create_index("ix_animal_rgn", "animal", ["rgn"])

    op.create_table(
        "avaliacao",
        *_sync_columns(),
        sa.Column(
            "animal_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("data_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("avaliador_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            status_avaliacao_ref,
            nullable=False,
            server_default=sa.text("'capturada'"),
        ),
        sa.Column("versao_pipeline", sa.String(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )

    op.create_table(
        "pesagem",
        *_sync_columns(),
        sa.Column(
            "animal_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("peso_kg", sa.Numeric(6, 2), nullable=False),
        sa.Column("origem", origem_pesagem_ref, nullable=False),
        sa.Column(
            "avaliacao_id",
            sa.Uuid(),
            sa.ForeignKey("avaliacao.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.create_table(
        "captura",
        *_sync_columns(),
        sa.Column(
            "avaliacao_id",
            sa.Uuid(),
            sa.ForeignKey("avaliacao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", tipo_captura_ref, nullable=False),
        sa.Column("vista", vista_captura_ref, nullable=False),
        sa.Column("arquivo_url", sa.String(), nullable=False),
        sa.Column("dispositivo", sa.String(), nullable=True),
        sa.Column("px_por_cm", sa.Numeric(8, 4), nullable=True),
        sa.Column("erro_calibracao_px", sa.Numeric(8, 4), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("captura")
    op.drop_table("pesagem")
    op.drop_table("avaliacao")
    op.drop_index("ix_animal_rgn", table_name="animal")
    op.drop_index("ix_animal_brinco", table_name="animal")
    op.drop_table("animal")
    op.drop_table("lote")
    op.drop_table("fazenda")

    bind = op.get_bind()
    for enum_name in (
        "vista_captura",
        "tipo_captura",
        "origem_pesagem",
        "status_avaliacao",
        "situacao_animal",
        "sexo",
        "variedade",
        "categoria_lote",
    ):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
