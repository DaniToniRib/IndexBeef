"""fase D: telemetria_gps, geofence, evento_geofence

Revision ID: 0006_gps_geofence
Revises: 0005_leitura_rfid
Create Date: 2026-11-02 00:00:00

Ver docs/11 §3. `poligono_wkt` ficaria como Geometry(POLYGON, 4326) em
Postgres+PostGIS; mantemos Text aqui para portabilidade com SQLite nos
testes — Shapely parseia WKT em qualquer dialeto.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_gps_geofence"
down_revision: str | None = "0005_leitura_rfid"
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

    estado = sa.Enum(
        "grazing", "walking", "resting", "desconhecido",
        name="estado_atividade_gps",
    )
    tipo_geofence = sa.Enum(
        "pasto", "limite", "alerta", "curral", name="tipo_geofence",
    )
    tipo_evento = sa.Enum("entrada", "saida", name="tipo_evento_geofence")
    for e in (estado, tipo_geofence, tipo_evento):
        e.create(bind, checkfirst=True)

    estado_ref = sa.Enum(
        "grazing", "walking", "resting", "desconhecido",
        name="estado_atividade_gps", create_type=False,
    )
    tipo_geofence_ref = sa.Enum(
        "pasto", "limite", "alerta", "curral",
        name="tipo_geofence", create_type=False,
    )
    tipo_evento_ref = sa.Enum(
        "entrada", "saida", name="tipo_evento_geofence", create_type=False,
    )

    op.create_table(
        "telemetria_gps",
        *_sync_columns(),
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
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("hdop", sa.Numeric(5, 2), nullable=True),
        sa.Column("bateria_pct", sa.Integer(), nullable=True),
        sa.Column("temperatura_c", sa.Numeric(4, 1), nullable=True),
        sa.Column("atividade", sa.Integer(), nullable=True),
        sa.Column("estado", estado_ref, nullable=True),
        sa.Column("rssi", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_telemetria_gps_animal_timestamp",
        "telemetria_gps",
        ["animal_id", "timestamp"],
    )

    op.create_table(
        "geofence",
        *_sync_columns(),
        sa.Column(
            "fazenda_id",
            sa.Uuid(),
            sa.ForeignKey("fazenda.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column(
            "tipo",
            tipo_geofence_ref,
            nullable=False,
            server_default=sa.text("'pasto'"),
        ),
        sa.Column("poligono_wkt", sa.Text(), nullable=False),
        sa.Column(
            "ativa",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("descricao", sa.Text(), nullable=True),
    )

    op.create_table(
        "evento_geofence",
        *_sync_columns(),
        sa.Column(
            "animal_id",
            sa.Uuid(),
            sa.ForeignKey("animal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "geofence_id",
            sa.Uuid(),
            sa.ForeignKey("geofence.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", tipo_evento_ref, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_evento_geofence_animal_timestamp",
        "evento_geofence",
        ["animal_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_evento_geofence_animal_timestamp", table_name="evento_geofence",
    )
    op.drop_table("evento_geofence")
    op.drop_table("geofence")
    op.drop_index(
        "ix_telemetria_gps_animal_timestamp", table_name="telemetria_gps",
    )
    op.drop_table("telemetria_gps")

    bind = op.get_bind()
    for name in ("tipo_evento_geofence", "tipo_geofence", "estado_atividade_gps"):
        sa.Enum(name=name).drop(bind, checkfirst=True)
