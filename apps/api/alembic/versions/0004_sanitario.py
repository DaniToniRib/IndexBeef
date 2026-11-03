"""fase C: campanha, aplicacao_sanitaria, atendimento_veterinario

Revision ID: 0004_sanitario
Revises: 0003_cadastros_dispositivos
Create Date: 2026-11-02 00:00:00

Ver docs/11 §4 e §5. CRMV obrigatorio em AtendimentoVeterinario (CFMV
1138/2016); em AplicacaoSanitaria o CRMV e opcional porque vermifugo
rotineiro pode ser aplicado pelo produtor — a validacao fica no schema.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_sanitario"
down_revision: str | None = "0003_cadastros_dispositivos"
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
    bind = op.get_bind()

    tipo_aplicacao = sa.Enum(
        "vacina", "vermifugo", "terapeutico", name="tipo_aplicacao_sanitaria",
    )
    via = sa.Enum("IM", "SC", "IV", "oral", "topico", "outra", name="via_administracao")
    status_campanha = sa.Enum(
        "planejada",
        "em_andamento",
        "concluida",
        "cancelada",
        name="status_campanha",
    )
    for e in (tipo_aplicacao, via, status_campanha):
        e.create(bind, checkfirst=True)

    tipo_aplicacao_ref = sa.Enum(
        "vacina",
        "vermifugo",
        "terapeutico",
        name="tipo_aplicacao_sanitaria",
        create_type=False,
    )
    via_ref = sa.Enum(
        "IM", "SC", "IV", "oral", "topico", "outra",
        name="via_administracao",
        create_type=False,
    )
    status_campanha_ref = sa.Enum(
        "planejada",
        "em_andamento",
        "concluida",
        "cancelada",
        name="status_campanha",
        create_type=False,
    )

    op.create_table(
        "campanha",
        *_sync_columns(),
        sa.Column(
            "fazenda_id",
            sa.Uuid(),
            sa.ForeignKey("fazenda.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("tipo", tipo_aplicacao_ref, nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=True),
        sa.Column("protocolo", sa.Text(), nullable=True),
        sa.Column(
            "status",
            status_campanha_ref,
            nullable=False,
            server_default=sa.text("'planejada'"),
        ),
    )

    op.create_table(
        "aplicacao_sanitaria",
        *_sync_columns(),
        sa.Column(
            "animal_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "campanha_id",
            sa.Uuid(),
            sa.ForeignKey("campanha.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tipo", tipo_aplicacao_ref, nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("principio_ativo", sa.String(), nullable=False),
        sa.Column("nome_comercial", sa.String(), nullable=True),
        sa.Column("concentracao", sa.String(), nullable=True),
        sa.Column("dose_ml", sa.Numeric(8, 3), nullable=True),
        sa.Column("dose_mg_por_kg", sa.Numeric(8, 3), nullable=True),
        sa.Column("via", via_ref, nullable=False),
        sa.Column("lote_medicamento", sa.String(), nullable=True),
        sa.Column("validade", sa.Date(), nullable=True),
        sa.Column("carencia_abate_dias", sa.Integer(), nullable=True),
        sa.Column("carencia_leite_dias", sa.Integer(), nullable=True),
        sa.Column("veterinario_crmv", sa.String(), nullable=True),
        sa.Column("veterinario_nome", sa.String(), nullable=True),
        sa.Column("receita_url", sa.String(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_aplicacao_sanitaria_animal_data",
        "aplicacao_sanitaria",
        ["animal_id", "data"],
    )

    op.create_table(
        "atendimento_veterinario",
        *_sync_columns(),
        sa.Column(
            "animal_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("data_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("veterinario_nome", sa.String(), nullable=False),
        sa.Column("veterinario_crmv", sa.String(), nullable=False),
        sa.Column("motivo", sa.String(), nullable=False),
        sa.Column("queixa", sa.Text(), nullable=True),
        sa.Column("peso_estimado_kg", sa.Numeric(6, 2), nullable=True),
        sa.Column("temperatura_c", sa.Numeric(4, 1), nullable=True),
        sa.Column("frequencia_cardiaca", sa.Integer(), nullable=True),
        sa.Column("frequencia_respiratoria", sa.Integer(), nullable=True),
        sa.Column("exame_fisico", sa.Text(), nullable=True),
        sa.Column("diagnostico", sa.Text(), nullable=True),
        sa.Column("prescricoes", sa.JSON(), nullable=True),
        sa.Column("receita_url", sa.String(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("atendimento_veterinario")
    op.drop_index(
        "ix_aplicacao_sanitaria_animal_data", table_name="aplicacao_sanitaria",
    )
    op.drop_table("aplicacao_sanitaria")
    op.drop_table("campanha")

    bind = op.get_bind()
    for name in ("status_campanha", "via_administracao", "tipo_aplicacao_sanitaria"):
        sa.Enum(name=name).drop(bind, checkfirst=True)
