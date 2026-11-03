"""fase2: tabelas de campo (escore_avaliacao, dados_geneticos, evento_reprodutivo, exame_andrologico)
e colunas manuais em medida_avaliacao

Revision ID: 0009_fase2_campo
Revises: 0008_avaliacao_estruturada
Create Date: 2026-11-03 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_fase2_campo"
down_revision: str | None = "0008_avaliacao_estruturada"
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
    # Enums novos
    tipo_evento_reprodutivo = sa.Enum(
        "cobertura",
        "iatf",
        "diagnostico_gestacao",
        "parto",
        "aborto",
        "desmama",
        name="tipo_evento_reprodutivo",
    )
    tipo_evento_reprodutivo.create(op.get_bind(), checkfirst=True)

    resultado_andrologico = sa.Enum(
        "apto",
        "inapto",
        "questionavel",
        name="resultado_andrologico",
    )
    resultado_andrologico.create(op.get_bind(), checkfirst=True)

    # Tabela escore_avaliacao
    op.create_table(
        "escore_avaliacao",
        *_sync_columns(),
        sa.Column(
            "avaliacao_id",
            sa.Uuid(),
            sa.ForeignKey("avaliacao.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("frame_score", sa.Numeric(4, 1), nullable=True),
        sa.Column("ecc_sugerido", sa.Numeric(3, 1), nullable=True),
        sa.Column("ecc_final", sa.Numeric(3, 1), nullable=True),
        sa.Column("e_sugerido", sa.SmallInteger(), nullable=True),
        sa.Column("e_final", sa.SmallInteger(), nullable=True),
        sa.Column("p_sugerido", sa.SmallInteger(), nullable=True),
        sa.Column("p_final", sa.SmallInteger(), nullable=True),
        sa.Column("m_sugerido", sa.SmallInteger(), nullable=True),
        sa.Column("m_final", sa.SmallInteger(), nullable=True),
        sa.Column("u_sugerido", sa.SmallInteger(), nullable=True),
        sa.Column("u_final", sa.SmallInteger(), nullable=True),
        sa.Column("r_sugerido", sa.SmallInteger(), nullable=True),
        sa.Column("r_final", sa.SmallInteger(), nullable=True),
        sa.Column("a_sugerido", sa.SmallInteger(), nullable=True),
        sa.Column("a_final", sa.SmallInteger(), nullable=True),
        sa.Column("s_sugerido", sa.SmallInteger(), nullable=True),
        sa.Column("s_final", sa.SmallInteger(), nullable=True),
    )

    # Tabela dados_geneticos
    op.create_table(
        "dados_geneticos",
        *_sync_columns(),
        sa.Column(
            "animal_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("programa", sa.String(), nullable=True),
        sa.Column("safra", sa.String(), nullable=True),
        sa.Column("deps", sa.JSON(), nullable=True),
        sa.Column("indice_programa", sa.Numeric(8, 3), nullable=True),
        sa.Column("deca", sa.SmallInteger(), nullable=True),
        sa.Column("data_importacao", sa.Date(), nullable=True),
    )

    # Tabela evento_reprodutivo
    op.create_table(
        "evento_reprodutivo",
        *_sync_columns(),
        sa.Column(
            "animal_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tipo",
            sa.Enum(
                "cobertura",
                "iatf",
                "diagnostico_gestacao",
                "parto",
                "aborto",
                "desmama",
                name="tipo_evento_reprodutivo",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("resultado", sa.Text(), nullable=True),
        sa.Column("dias_gestacao", sa.Integer(), nullable=True),
        sa.Column(
            "touro_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "bezerro_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("peso_desmama_bezerro", sa.Numeric(7, 2), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )

    # Tabela exame_andrologico
    op.create_table(
        "exame_andrologico",
        *_sync_columns(),
        sa.Column(
            "animal_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("perimetro_escrotal_cm", sa.Numeric(5, 1), nullable=True),
        sa.Column(
            "resultado",
            sa.Enum(
                "apto",
                "inapto",
                "questionavel",
                name="resultado_andrologico",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("veterinario", sa.String(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )

    # Colunas manuais em medida_avaliacao
    op.add_column(
        "medida_avaliacao",
        sa.Column("altura_cernelha_manual_cm", sa.Numeric(7, 2), nullable=True),
    )
    op.add_column(
        "medida_avaliacao",
        sa.Column("altura_garupa_manual_cm", sa.Numeric(7, 2), nullable=True),
    )
    op.add_column(
        "medida_avaliacao",
        sa.Column("comprimento_corporal_manual_cm", sa.Numeric(7, 2), nullable=True),
    )
    op.add_column(
        "medida_avaliacao",
        sa.Column("largura_garupa_manual_cm", sa.Numeric(7, 2), nullable=True),
    )
    op.add_column(
        "medida_avaliacao",
        sa.Column("perimetro_toracico_manual_cm", sa.Numeric(7, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("medida_avaliacao", "perimetro_toracico_manual_cm")
    op.drop_column("medida_avaliacao", "largura_garupa_manual_cm")
    op.drop_column("medida_avaliacao", "comprimento_corporal_manual_cm")
    op.drop_column("medida_avaliacao", "altura_garupa_manual_cm")
    op.drop_column("medida_avaliacao", "altura_cernelha_manual_cm")
    op.drop_table("exame_andrologico")
    op.drop_table("evento_reprodutivo")
    op.drop_table("dados_geneticos")
    op.drop_table("escore_avaliacao")
    sa.Enum(name="resultado_andrologico").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tipo_evento_reprodutivo").drop(op.get_bind(), checkfirst=True)
