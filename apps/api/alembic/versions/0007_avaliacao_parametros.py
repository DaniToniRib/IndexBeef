"""avaliacao: adiciona parametros_entrada (JSON)

Revision ID: 0007_avaliacao_parametros
Revises: 0006_gps_geofence
Create Date: 2026-11-03 00:00:00

Guarda os parametros de entrada (keypoints, sexo, idade_meses, etc.) para
que a task RQ possa processar em segundo plano sem precisar do request HTTP.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_avaliacao_parametros"
down_revision: str | None = "0006_gps_geofence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("avaliacao", sa.Column("parametros_entrada", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("avaliacao", "parametros_entrada")
