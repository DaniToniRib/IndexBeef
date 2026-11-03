"""Deteccao de eventos de geofence (entrada/saida) via Shapely.

Em producao com PostGIS, substituir por ST_Contains direto no banco com
indice GiST (ver docs/11 §6). Aqui mantemos pure Python para portabilidade.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from shapely.geometry import Point
from shapely.wkt import loads as wkt_loads
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evento_geofence import EventoGeofence
from app.models.geofence import Geofence
from app.models.telemetria_gps import TelemetriaGps


def ponto_dentro(poligono_wkt: str, lat: Decimal | float, lon: Decimal | float) -> bool:
    poligono = wkt_loads(poligono_wkt)
    return poligono.contains(Point(float(lon), float(lat)))


def _ultimo_ponto_anterior(
    db: Session, animal_id: uuid.UUID, ts: datetime,
) -> TelemetriaGps | None:
    stmt = (
        select(TelemetriaGps)
        .where(TelemetriaGps.animal_id == animal_id)
        .where(TelemetriaGps.timestamp < ts)
        .order_by(TelemetriaGps.timestamp.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def processar_ponto(
    db: Session, ponto: TelemetriaGps, geofences: list[Geofence],
) -> list[EventoGeofence]:
    """Gera eventos de entrada/saida comparando `ponto` com o ponto anterior.

    - Entrada: estava fora e entrou
    - Saida: estava dentro e saiu
    - Primeiro ponto de um animal: so entra se dentro (sem evento de saida).

    Nao faz commit — apenas adiciona os EventoGeofence a sessao.
    """
    if ponto.animal_id is None:
        return []

    anterior = _ultimo_ponto_anterior(db, ponto.animal_id, ponto.timestamp)
    eventos: list[EventoGeofence] = []
    for gf in geofences:
        if not gf.ativa:
            continue
        try:
            dentro_agora = ponto_dentro(gf.poligono_wkt, ponto.latitude, ponto.longitude)
        except Exception:  # noqa: BLE001 — WKT invalido no banco: pula
            continue
        dentro_antes = (
            ponto_dentro(gf.poligono_wkt, anterior.latitude, anterior.longitude)
            if anterior is not None
            else False
        )
        tipo = None
        if dentro_agora and not dentro_antes:
            tipo = "entrada"
        elif dentro_antes and not dentro_agora:
            tipo = "saida"
        if tipo is not None:
            evento = EventoGeofence(
                animal_id=ponto.animal_id,
                geofence_id=gf.id,
                tipo=tipo,
                timestamp=ponto.timestamp,
            )
            db.add(evento)
            eventos.append(evento)
    return eventos


def detectar_alertas(
    ponto: TelemetriaGps, limite_bateria: int = 15,
) -> list[dict[str, str]]:
    """Retorna alertas derivados do ponto (bateria baixa etc)."""
    alertas: list[dict[str, str]] = []
    if ponto.bateria_pct is not None and ponto.bateria_pct <= limite_bateria:
        alertas.append(
            {
                "tipo": "bateria_baixa",
                "detalhe": f"bateria={ponto.bateria_pct}% (<= {limite_bateria}%)",
            },
        )
    return alertas
