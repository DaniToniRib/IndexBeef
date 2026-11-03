"""avaliacao: tabelas estruturadas de resultado

Revision ID: 0008_avaliacao_estruturada
Revises: 0007_avaliacao_parametros
Create Date: 2026-11-03 00:00:00

Implementa as tabelas medida_avaliacao, caixa_virtual_avaliacao e
predicao_avaliacao descritas em docs/06. A coluna avaliacao.resultado (JSONB)
permanece como archive enquanto todas as queries migram para as novas tabelas.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_avaliacao_estruturada"
down_revision: str | None = "0007_avaliacao_parametros"
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
    op.create_table(
        "medida_avaliacao",
        *_sync_columns(),
        sa.Column(
            "avaliacao_id",
            sa.Uuid(),
            sa.ForeignKey("avaliacao.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("altura_cernelha_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("altura_cernelha_conf", sa.Numeric(5, 4), nullable=True),
        sa.Column("altura_garupa_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("altura_garupa_conf", sa.Numeric(5, 4), nullable=True),
        sa.Column("comprimento_corporal_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("comprimento_corporal_conf", sa.Numeric(5, 4), nullable=True),
        sa.Column("profundidade_toracica_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("profundidade_toracica_conf", sa.Numeric(5, 4), nullable=True),
        sa.Column("comprimento_garupa_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("comprimento_garupa_conf", sa.Numeric(5, 4), nullable=True),
        sa.Column("largura_garupa_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("largura_garupa_conf", sa.Numeric(5, 4), nullable=True),
        sa.Column("altura_cupim_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("altura_cupim_conf", sa.Numeric(5, 4), nullable=True),
        sa.Column("umbigo_chao_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("umbigo_chao_conf", sa.Numeric(5, 4), nullable=True),
        sa.Column("perimetro_toracico_est_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("perimetro_toracico_est_conf", sa.Numeric(5, 4), nullable=True),
        sa.Column("inclinacao_garupa_graus", sa.Numeric(6, 2), nullable=True),
        sa.Column("jarrete_graus", sa.Numeric(6, 2), nullable=True),
    )

    op.create_table(
        "caixa_virtual_avaliacao",
        *_sync_columns(),
        sa.Column(
            "avaliacao_id",
            sa.Uuid(),
            sa.ForeignKey("avaliacao.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("c_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("p_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("l_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("volume_cm3", sa.Numeric(10, 2), nullable=True),
        sa.Column("volume_l", sa.Numeric(8, 2), nullable=True),
        sa.Column("ipl", sa.Numeric(6, 4), nullable=True),
        sa.Column("compacidade", sa.Numeric(6, 4), nullable=True),
        sa.Column("indice_comprimento", sa.Numeric(6, 4), nullable=True),
    )

    op.create_table(
        "predicao_avaliacao",
        *_sync_columns(),
        sa.Column(
            "avaliacao_id",
            sa.Uuid(),
            sa.ForeignKey("avaliacao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("valor", sa.Numeric(8, 2), nullable=True),
        sa.Column("faixa_min", sa.Numeric(8, 2), nullable=True),
        sa.Column("faixa_max", sa.Numeric(8, 2), nullable=True),
        sa.Column("confianca", sa.Numeric(5, 4), nullable=True),
        sa.Column("metodo", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_predicao_avaliacao_avaliacao_tipo",
        "predicao_avaliacao",
        ["avaliacao_id", "tipo"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_predicao_avaliacao_avaliacao_tipo", table_name="predicao_avaliacao",
    )
    op.drop_table("predicao_avaliacao")
    op.drop_table("caixa_virtual_avaliacao")
    op.drop_table("medida_avaliacao")
