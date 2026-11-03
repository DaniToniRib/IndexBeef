"""fase B: tabela leitura_rfid (staging de bastao/antena)

Revision ID: 0005_leitura_rfid
Revises: 0004_sanitario
Create Date: 2026-11-02 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_leitura_rfid"
down_revision: str | None = "0004_sanitario"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "leitura_rfid",
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
        sa.Column(
            "dispositivo_id",
            sa.Uuid(),
            sa.ForeignKey("dispositivo.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "animal_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("eid", sa.String(length=32), nullable=False),
        sa.Column("vid", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session", sa.String(), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("pareado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_leitura_rfid_eid", "leitura_rfid", ["eid"])
    op.create_index("ix_leitura_rfid_vid", "leitura_rfid", ["vid"])


def downgrade() -> None:
    op.drop_index("ix_leitura_rfid_vid", table_name="leitura_rfid")
    op.drop_index("ix_leitura_rfid_eid", table_name="leitura_rfid")
    op.drop_table("leitura_rfid")
