"""adiciona coluna resultado (JSON) em avaliacao

Revision ID: 0002_avaliacao_resultado
Revises: 0001_inicial
Create Date: 2026-11-02 00:00:00

Guarda o payload do pipeline (indexbeef_vision.pipeline.montar_payload) na
tabela avaliacao enquanto nao migramos para as tabelas estruturadas do
docs/06 (medidas, caixa_virtual, escores, predicao). Portavel: SQLAlchemy
sa.JSON vira JSONB no Postgres e TEXT no SQLite.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_avaliacao_resultado"
down_revision: str | None = "0001_inicial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "avaliacao",
        sa.Column("resultado", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("avaliacao", "resultado")
