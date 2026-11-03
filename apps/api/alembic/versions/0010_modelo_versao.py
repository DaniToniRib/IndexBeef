"""modelo_versao: tabela de registro de versoes de modelos ML

Revision ID: 0010_modelo_versao
Revises: 0009_fase2_campo
Create Date: 2026-11-03 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_modelo_versao"
down_revision: str | None = "0009_fase2_campo"
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
        "modelo_versao",
        *_sync_columns(),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("versao", sa.String(), nullable=False),
        sa.Column("metricas", sa.JSON(), nullable=True),
        sa.Column("artefato_url", sa.String(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("descricao", sa.Text(), nullable=True),
    )
    op.create_index("ix_modelo_versao_nome", "modelo_versao", ["nome"])


def downgrade() -> None:
    op.drop_index("ix_modelo_versao_nome", table_name="modelo_versao")
    op.drop_table("modelo_versao")
