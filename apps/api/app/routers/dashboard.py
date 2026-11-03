"""Dashboard agregado por fazenda.

GET /fazendas/{fazenda_id}/dashboard      — visao geral: totais, alertas de bateria,
                                            animais fora da cerca, campanhas ativas,
                                            pesagens e avaliacoes recentes.
GET /fazendas/{fazenda_id}/painel-remoto  — painel simplificado para o criador ver
                                            remotamente (Fase 5).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
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
from app.models.escore_avaliacao import EscoreAvaliacao
from app.models.evento_geofence import EventoGeofence
from app.models.fazenda import Fazenda
from app.models.geofence import Geofence
from app.models.lote import Lote
from app.models.pesagem import Pesagem
from app.models.predicao_avaliacao import PredicaoAvaliacao
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


# ---------------------------------------------------------------------------
# Painel remoto para o criador (Fase 5)
# ---------------------------------------------------------------------------


@router.get("/fazendas/{fazenda_id}/painel-remoto")
def painel_remoto(
    fazenda_id: uuid.UUID, db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Visao simplificada para o criador acompanhar a fazenda remotamente."""
    fazenda = db.get(Fazenda, fazenda_id)
    if fazenda is None:
        raise HTTPException(status_code=404, detail="fazenda nao encontrada")

    agora = datetime.now(UTC)
    ha90dias = (agora - timedelta(days=90)).date()

    # Totais
    total_animais: int = db.scalar(
        select(func.count(Animal.id)).where(Animal.fazenda_id == fazenda_id),
    ) or 0
    total_lotes: int = db.scalar(
        select(func.count(Lote.id)).where(Lote.fazenda_id == fazenda_id),
    ) or 0

    # Ultimas 10 avaliacoes (mais recentes)
    ultimas_avaliacoes_rows = db.execute(
        select(
            Animal.brinco,
            Avaliacao.data_hora,
            PredicaoAvaliacao.valor.label("peso_estimado_kg"),
            PredicaoAvaliacao.valor.label("indice_garrote_val"),
        )
        .join(Animal, Animal.id == Avaliacao.animal_id)
        .outerjoin(
            PredicaoAvaliacao,
            (PredicaoAvaliacao.avaliacao_id == Avaliacao.id)
            & (PredicaoAvaliacao.tipo == "peso_atual"),
        )
        .where(Animal.fazenda_id == fazenda_id)
        .order_by(Avaliacao.data_hora.desc())
        .limit(10),
    ).all()

    # Busca indice_garrote separado para as ultimas avaliacoes
    avaliacoes_ids: list[uuid.UUID] = []
    if ultimas_avaliacoes_rows:
        avaliacoes_ids_rows = db.execute(
            select(Avaliacao.id, Animal.brinco, Avaliacao.data_hora)
            .join(Animal, Animal.id == Avaliacao.animal_id)
            .where(Animal.fazenda_id == fazenda_id)
            .order_by(Avaliacao.data_hora.desc())
            .limit(10),
        ).all()
        avaliacoes_ids = [r[0] for r in avaliacoes_ids_rows]

    # Monta lista de ultimas avaliacoes
    ultimas_avaliacoes = []
    for r in avaliacoes_ids[:10]:
        avaliacao = db.get(Avaliacao, r)
        if avaliacao is None:
            continue
        animal = db.get(Animal, avaliacao.animal_id)
        pred_peso = db.scalar(
            select(PredicaoAvaliacao)
            .where(PredicaoAvaliacao.avaliacao_id == avaliacao.id)
            .where(PredicaoAvaliacao.tipo == "peso_atual"),
        )
        pred_idx = db.scalar(
            select(PredicaoAvaliacao)
            .where(PredicaoAvaliacao.avaliacao_id == avaliacao.id)
            .where(PredicaoAvaliacao.tipo == "indice_garrote"),
        )
        ultimas_avaliacoes.append({
            "animal_brinco": animal.brinco if animal else None,
            "data": avaliacao.data_hora.isoformat(),
            "peso_estimado_kg": float(pred_peso.valor) if pred_peso and pred_peso.valor else None,
            "indice_garrote": float(pred_idx.valor) if pred_idx and pred_idx.valor else None,
        })

    # Alertas ECC (ECC < 3.5 ou > 8.5)
    alertas_ecc_rows = db.execute(
        select(Animal.brinco, Avaliacao.data_hora, EscoreAvaliacao.ecc_final)
        .join(Avaliacao, Avaliacao.animal_id == Animal.id)
        .join(EscoreAvaliacao, EscoreAvaliacao.avaliacao_id == Avaliacao.id)
        .where(Animal.fazenda_id == fazenda_id)
        .where(
            (EscoreAvaliacao.ecc_final < 3.5) | (EscoreAvaliacao.ecc_final > 8.5),
        )
        .order_by(Avaliacao.data_hora.desc())
        .limit(50),
    ).all()

    alertas_ecc = [
        {
            "animal_brinco": r[0],
            "data": r[1].isoformat() if r[1] else None,
            "ecc": float(r[2]) if r[2] is not None else None,
        }
        for r in alertas_ecc_rows
    ]

    # Peso medio por lote (somente lotes com pesagem nos ultimos 90 dias)
    lotes_rows = db.scalars(
        select(Lote).where(Lote.fazenda_id == fazenda_id),
    ).all()

    peso_medio_lote = []
    for lote in lotes_rows:
        stats = db.execute(
            select(func.avg(Pesagem.peso_kg), func.count(Pesagem.id))
            .join(Animal, Animal.id == Pesagem.animal_id)
            .where(Animal.lote_id == lote.id)
            .where(Pesagem.data >= ha90dias),
        ).one()
        n_animais = stats[1] or 0
        if n_animais > 0:
            peso_medio_lote.append({
                "lote_nome": lote.nome,
                "categoria": str(lote.categoria.value if hasattr(lote.categoria, "value") else lote.categoria),
                "peso_medio_kg": float(stats[0]) if stats[0] is not None else None,
                "n_animais": n_animais,
            })

    return {
        "fazenda": {
            "id": str(fazenda.id),
            "nome": fazenda.nome,
            "municipio": fazenda.municipio,
            "uf": fazenda.uf,
        },
        "totais": {
            "animais": total_animais,
            "lotes": total_lotes,
        },
        "ultimas_avaliacoes": ultimas_avaliacoes,
        "alertas_ecc": alertas_ecc,
        "peso_medio_lote": peso_medio_lote,
    }
