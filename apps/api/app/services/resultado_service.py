"""Persiste o resultado do pipeline nas tabelas estruturadas + JSONB."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.avaliacao import Avaliacao
from app.models.caixa_virtual_avaliacao import CaixaVirtualAvaliacao
from app.models.medida_avaliacao import MedidaAvaliacao
from app.models.predicao_avaliacao import PredicaoAvaliacao


def _f(d: dict, key: str) -> float | None:
    v = d.get(key)
    return float(v) if v is not None else None


def salvar_resultado_estruturado(
    db: Session,
    avaliacao: Avaliacao,
    resultado: dict[str, Any],
) -> None:
    """Salva o payload do pipeline nas tabelas medida_avaliacao, caixa_virtual_avaliacao
    e predicao_avaliacao. Chamado tanto pelo path sincrono (router) quanto pelo worker."""
    mc = resultado.get("medidas_cm", {})
    ang = resultado.get("angulos_graus", {})

    def mv(nome: str) -> float | None:
        return _f(mc.get(nome, {}), "valor") if isinstance(mc.get(nome), dict) else None

    def mc_(nome: str) -> float | None:
        return _f(mc.get(nome, {}), "confianca") if isinstance(mc.get(nome), dict) else None

    medida = MedidaAvaliacao(
        avaliacao_id=avaliacao.id,
        altura_cernelha_cm=mv("altura_cernelha"),
        altura_cernelha_conf=mc_("altura_cernelha"),
        altura_garupa_cm=mv("altura_garupa"),
        altura_garupa_conf=mc_("altura_garupa"),
        comprimento_corporal_cm=mv("comprimento_corporal"),
        comprimento_corporal_conf=mc_("comprimento_corporal"),
        profundidade_toracica_cm=mv("profundidade_toracica"),
        profundidade_toracica_conf=mc_("profundidade_toracica"),
        comprimento_garupa_cm=mv("comprimento_garupa"),
        comprimento_garupa_conf=mc_("comprimento_garupa"),
        largura_garupa_cm=mv("largura_garupa"),
        largura_garupa_conf=mc_("largura_garupa"),
        altura_cupim_cm=mv("altura_cupim"),
        altura_cupim_conf=mc_("altura_cupim"),
        umbigo_chao_cm=mv("umbigo_chao"),
        umbigo_chao_conf=mc_("umbigo_chao"),
        perimetro_toracico_est_cm=mv("perimetro_toracico_est"),
        perimetro_toracico_est_conf=mc_("perimetro_toracico_est"),
        inclinacao_garupa_graus=ang.get("inclinacao_garupa"),
        jarrete_graus=ang.get("jarrete"),
    )
    db.add(medida)

    cv = resultado.get("caixa_virtual", {})
    caixa = CaixaVirtualAvaliacao(
        avaliacao_id=avaliacao.id,
        c_cm=cv.get("C"),
        p_cm=cv.get("P"),
        l_cm=cv.get("L"),
        volume_cm3=cv.get("volume_cm3"),
        volume_l=cv.get("volume_l"),
        ipl=cv.get("ipl"),
        compacidade=cv.get("compacidade"),
        indice_comprimento=cv.get("indice_comprimento"),
    )
    db.add(caixa)

    peso = resultado.get("peso", {})
    if peso.get("peso_kg") is not None:
        db.add(PredicaoAvaliacao(
            avaliacao_id=avaliacao.id,
            tipo="peso_atual",
            valor=peso["peso_kg"],
            metodo=peso.get("metodo"),
        ))

    for pt in resultado.get("projecao_peso", {}).get("pontos", []):
        db.add(PredicaoAvaliacao(
            avaliacao_id=avaliacao.id,
            tipo=f"peso_{int(pt['idade_meses'])}m",
            valor=pt["peso_kg"],
            faixa_min=pt["peso_min_kg"],
            faixa_max=pt["peso_max_kg"],
        ))
