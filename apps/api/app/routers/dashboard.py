"""Dashboard agregado por fazenda.

GET /fazendas/{fazenda_id}/dashboard — visao geral: totais, alertas de bateria,
animais fora da cerca, campanhas ativas, pesagens e avaliacoes recentes.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.animal import Animal
from app.models.avaliacao import Avaliacao
from app.models.campanha import Campanha
from app.models.dispositivo import Dispositivo
from app.models.enums import StatusCampanha
from app.models.evento_geofence import EventoGeofence
from app.models.fazenda import Fazenda
from app.models.geofence import Geofence
from app.models.pesagem import Pesagem
from app.models.telemetria_gps import TelemetriaGps

router = APIRouter(tags=["dashboard"])


@router.get("/fazendas/{fazenda_id}/dashboard")
def dashboard_fazenda(
    fazenda_id: uuid.UUID, db: Session = Depends(get_db),
) -> dict[str, Any]:
    fazenda = db.get(Fazenda, fazenda_id)
    if fazenda is None:
        raise HTTPException(status_code=404, detail="fazenda nao encontrada")

    agora = datetime.now(UTC)
    ha7dias = agora - timedelta(days=7)

    # Totais de animais
    total_animais: int = db.scalar(
        select(func.count(Animal.id)).where(Animal.fazenda_id == fazenda_id),
    ) or 0

    animais_por_sexo_rows = db.execute(
        select(Animal.sexo, func.count(Animal.id))
        .where(Animal.fazenda_id == fazenda_id)
        .group_by(Animal.sexo),
    ).all()
    animais_por_sexo = {str(r[0].value if hasattr(r[0], "value") else r[0]): r[1]
                        for r in animais_por_sexo_rows}

    # Campanhas ativas
    campanhas_ativas: int = db.scalar(
        select(func.count(Campanha.id))
        .where(Campanha.fazenda_id == fazenda_id)
        .where(Campanha.status == StatusCampanha.em_andamento),
    ) or 0

    # Pesagens ultimos 7 dias
    pesagens_recentes: int = db.scalar(
        select(func.count(Pesagem.id))
        .join(Animal, Animal.id == Pesagem.animal_id)
        .where(Animal.fazenda_id == fazenda_id)
        .where(Pesagem.data >= ha7dias.date()),
    ) or 0

    # Avaliacoes ultimos 7 dias
    avaliacoes_semana: int = db.scalar(
        select(func.count(Avaliacao.id))
        .join(Animal, Animal.id == Avaliacao.animal_id)
        .where(Animal.fazenda_id == fazenda_id)
        .where(Avaliacao.data_hora >= ha7dias),
    ) or 0

    # Alertas de bateria: dispositivos GPS com ultimo ponto bateria <= 15%
    alertas_bateria = []
    dispositivos_gps = db.scalars(
        select(Dispositivo).where(Dispositivo.fazenda_id == fazenda_id),
    ).all()
    for disp in dispositivos_gps:
        ultimo_ponto = db.scalar(
            select(TelemetriaGps)
            .where(TelemetriaGps.dispositivo_id == disp.id)
            .order_by(TelemetriaGps.timestamp.desc())
            .limit(1),
        )
        if ultimo_ponto and ultimo_ponto.bateria_pct is not None and ultimo_ponto.bateria_pct <= 15:
            animal_brinco = None
            if ultimo_ponto.animal_id:
                a = db.get(Animal, ultimo_ponto.animal_id)
                animal_brinco = a.brinco if a else None
            alertas_bateria.append({
                "dispositivo_id": str(disp.id),
                "dispositivo_modelo": disp.modelo,
                "animal_id": str(ultimo_ponto.animal_id) if ultimo_ponto.animal_id else None,
                "animal_brinco": animal_brinco,
                "bateria_pct": int(ultimo_ponto.bateria_pct),
                "timestamp": ultimo_ponto.timestamp.isoformat(),
            })

    # Animais fora da cerca: ultimo evento_geofence de cada animal e tipo=saida
    animais_fazenda_ids = db.scalars(
        select(Animal.id).where(Animal.fazenda_id == fazenda_id),
    ).all()

    animais_fora = []
    for animal_id in animais_fazenda_ids:
        ultimo_ev = db.scalar(
            select(EventoGeofence)
            .where(EventoGeofence.animal_id == animal_id)
            .order_by(EventoGeofence.timestamp.desc())
            .limit(1),
        )
        tipo_str = str(
            ultimo_ev.tipo.value if hasattr(ultimo_ev.tipo, "value") else ultimo_ev.tipo,
        )
        if ultimo_ev and tipo_str == "saida":
            a = db.get(Animal, animal_id)
            gf = db.get(Geofence, ultimo_ev.geofence_id)
            animais_fora.append({
                "animal_id": str(animal_id),
                "animal_brinco": a.brinco if a else None,
                "geofence_id": str(ultimo_ev.geofence_id),
                "geofence_nome": gf.nome if gf else None,
                "saida_em": ultimo_ev.timestamp.isoformat(),
            })

    # Geofences da fazenda para o mapa
    geofences_rows = db.scalars(
        select(Geofence)
        .where(Geofence.fazenda_id == fazenda_id)
        .where(Geofence.ativa.is_(True)),
    ).all()
    geofences = [
        {
            "id": str(g.id),
            "nome": g.nome,
            "tipo": str(g.tipo.value if hasattr(g.tipo, "value") else g.tipo),
            "poligono_wkt": g.poligono_wkt,
        }
        for g in geofences_rows
    ]

    return {
        "fazenda_id": str(fazenda_id),
        "fazenda_nome": fazenda.nome,
        "total_animais": total_animais,
        "animais_por_sexo": animais_por_sexo,
        "campanhas_ativas": campanhas_ativas,
        "pesagens_recentes_7d": pesagens_recentes,
        "avaliacoes_semana": avaliacoes_semana,
        "alertas_bateria": alertas_bateria,
        "animais_fora_cerca": animais_fora,
        "geofences": geofences,
    }
