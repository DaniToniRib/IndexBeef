"""fase5_auth: tabelas usuario e fazenda_usuario para autenticacao e papeis

Revision ID: 0012_fase5_auth
Revises: 0011_fase4_indices
Create Date: 2026-11-03 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_fase5_auth"
down_revision: str | None = "0011_fase4_indices"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _sync_columns() -> list[sa.Column]:
    return [
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("origem_estacao", sa.String(), nullable=True),
        sa.Column("sincronizado_em", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("senha_hash", sa.String(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_sync_columns(),
    )
    op.create_index("ix_usuario_email", "usuario", ["email"], unique=True)

    op.create_table(
        "fazenda_usuario",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("fazenda_id", sa.Uuid(), sa.ForeignKey("fazenda.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("papel", sa.String(), nullable=False),
        *_sync_columns(),
        sa.UniqueConstraint("fazenda_id", "usuario_id", name="uq_fazenda_usuario"),
    )


def downgrade() -> None:
    op.drop_table("fazenda_usuario")
    op.drop_index("ix_usuario_email", table_name="usuario")
    op.drop_table("usuario")
