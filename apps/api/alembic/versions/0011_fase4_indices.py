"""fase4_indices: adiciona explicacao e modelo_versao_id em predicao_avaliacao

Revision ID: 0011_fase4_indices
Revises: 0010_modelo_versao
Create Date: 2026-11-03 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_fase4_indices"
down_revision: str | None = "0010_modelo_versao"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "predicao_avaliacao",
        sa.Column("explicacao", sa.JSON(), nullable=True),
    )
    op.add_column(
        "predicao_avaliacao",
        sa.Column("modelo_versao_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_predicao_avaliacao_modelo_versao",
        "predicao_avaliacao",
        "modelo_versao",
        ["modelo_versao_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_predicao_avaliacao_modelo_versao",
        "predicao_avaliacao",
        type_="foreignkey",
    )
    op.drop_column("predicao_avaliacao", "modelo_versao_id")
    op.drop_column("predicao_avaliacao", "explicacao")
