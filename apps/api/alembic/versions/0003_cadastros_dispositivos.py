"""fase A: tipo em fazenda, IdentificacaoEletronica, Dispositivo, campos extras

Revision ID: 0003_cadastros_dispositivos
Revises: 0002_avaliacao_resultado
Create Date: 2026-11-02 00:00:00

Fase A da expansao de pecuaria (ver docs/11 §6):

- fazenda ganha: tipo (enum), latitude, longitude, area_hectares,
  codigo_sisbov, inscricao_estadual
- animal ganha: data_entrada, observacoes
- identificacao_eletronica (nova): botton RFID / brinco eletronico
  separado de Animal, permite historico de trocas
- dispositivo (nova): balanca, bastao RFID, GPS tracker da fazenda
- pesagem ganha: dispositivo_id (auditoria do pareamento)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_cadastros_dispositivos"
down_revision: str | None = "0002_avaliacao_resultado"
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

    # Novos enums
    tipo_fazenda = sa.Enum(
        "fazenda", "sitio", "retiro", "outro", name="tipo_fazenda",
    )
    modo_rfid = sa.Enum("FDX_B", "HDX", name="modo_rfid")
    tipo_dispositivo = sa.Enum(
        "balanca",
        "bastao_rfid",
        "antena_rfid_brete",
        "gps_tracker",
        "camera",
        "outro",
        name="tipo_dispositivo",
    )
    status_dispositivo = sa.Enum(
        "ativo", "inativo", "manutencao", name="status_dispositivo",
    )
    for enum_type in (tipo_fazenda, modo_rfid, tipo_dispositivo, status_dispositivo):
        enum_type.create(bind, checkfirst=True)

    tipo_fazenda_ref = sa.Enum(
        "fazenda", "sitio", "retiro", "outro", name="tipo_fazenda", create_type=False,
    )
    modo_rfid_ref = sa.Enum("FDX_B", "HDX", name="modo_rfid", create_type=False)
    tipo_dispositivo_ref = sa.Enum(
        "balanca",
        "bastao_rfid",
        "antena_rfid_brete",
        "gps_tracker",
        "camera",
        "outro",
        name="tipo_dispositivo",
        create_type=False,
    )
    status_dispositivo_ref = sa.Enum(
        "ativo",
        "inativo",
        "manutencao",
        name="status_dispositivo",
        create_type=False,
    )

    # Fazenda: campos novos
    op.add_column(
        "fazenda",
        sa.Column(
            "tipo",
            tipo_fazenda_ref,
            nullable=False,
            server_default=sa.text("'fazenda'"),
        ),
    )
    op.add_column("fazenda", sa.Column("latitude", sa.Numeric(9, 6), nullable=True))
    op.add_column("fazenda", sa.Column("longitude", sa.Numeric(9, 6), nullable=True))
    op.add_column(
        "fazenda", sa.Column("area_hectares", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column("fazenda", sa.Column("codigo_sisbov", sa.String(), nullable=True))
    op.add_column("fazenda", sa.Column("inscricao_estadual", sa.String(), nullable=True))

    # Animal: campos novos
    op.add_column("animal", sa.Column("data_entrada", sa.Date(), nullable=True))
    op.add_column("animal", sa.Column("observacoes", sa.Text(), nullable=True))

    # Nova tabela: identificacao_eletronica
    op.create_table(
        "identificacao_eletronica",
        *_sync_columns(),
        sa.Column(
            "animal_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("eid", sa.String(length=32), nullable=False),
        sa.Column("vid", sa.String(), nullable=True),
        sa.Column(
            "modo",
            modo_rfid_ref,
            nullable=False,
            server_default=sa.text("'FDX_B'"),
        ),
        sa.Column("fabricante", sa.String(), nullable=True),
        sa.Column(
            "ativo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("ativo_desde", sa.Date(), nullable=False),
        sa.Column("inativo_desde", sa.Date(), nullable=True),
        sa.Column("motivo_troca", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_identificacao_eletronica_eid", "identificacao_eletronica", ["eid"],
    )
    op.create_index(
        "ix_identificacao_eletronica_vid", "identificacao_eletronica", ["vid"],
    )

    # Nova tabela: dispositivo
    op.create_table(
        "dispositivo",
        *_sync_columns(),
        sa.Column(
            "fazenda_id",
            sa.Uuid(),
            sa.ForeignKey("fazenda.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", tipo_dispositivo_ref, nullable=False),
        sa.Column("modelo", sa.String(), nullable=True),
        sa.Column("fabricante", sa.String(), nullable=True),
        sa.Column("numero_serie", sa.String(), nullable=True),
        sa.Column("data_instalacao", sa.Date(), nullable=True),
        sa.Column(
            "status",
            status_dispositivo_ref,
            nullable=False,
            server_default=sa.text("'ativo'"),
        ),
        sa.Column("config", sa.JSON(), nullable=True),
    )
    op.create_index("ix_dispositivo_numero_serie", "dispositivo", ["numero_serie"])

    # Pesagem: dispositivo_id (auditoria do pareamento)
    op.add_column(
        "pesagem",
        sa.Column(
            "dispositivo_id",
            sa.Uuid(),
            sa.ForeignKey("dispositivo.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("pesagem", "dispositivo_id")
    op.drop_index("ix_dispositivo_numero_serie", table_name="dispositivo")
    op.drop_table("dispositivo")
    op.drop_index(
        "ix_identificacao_eletronica_vid", table_name="identificacao_eletronica",
    )
    op.drop_index(
        "ix_identificacao_eletronica_eid", table_name="identificacao_eletronica",
    )
    op.drop_table("identificacao_eletronica")
    op.drop_column("animal", "observacoes")
    op.drop_column("animal", "data_entrada")
    op.drop_column("fazenda", "inscricao_estadual")
    op.drop_column("fazenda", "codigo_sisbov")
    op.drop_column("fazenda", "area_hectares")
    op.drop_column("fazenda", "longitude")
    op.drop_column("fazenda", "latitude")
    op.drop_column("fazenda", "tipo")

    bind = op.get_bind()
    for name in ("status_dispositivo", "tipo_dispositivo", "modo_rfid", "tipo_fazenda"):
        sa.Enum(name=name).drop(bind, checkfirst=True)
