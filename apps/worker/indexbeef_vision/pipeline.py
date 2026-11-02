"""Orquestracao do pipeline da Fase 0.

A Fase 0 processa a partir de **keypoints ja em cm** (apos o tecnico clicar
e `calibration.pixel_para_cm` converter). Nao executa deteccao/segmentacao
automatica aqui — isso vem na Fase 1 quando houver modelo de pose treinado
com os dados do Pantanal.

`montar_payload` e **pura**: so recebe medidas/calibracao/metadados e
devolve o dict JSON unificado conforme docs/04 "Saida do pipeline" +
extensoes para peso (docs/05 §1) e projecao (docs/05 §2).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from indexbeef_vision.calibration import Calibracao
from indexbeef_vision.measurements import Keypoints, medir
from indexbeef_vision.projection import (
    FAIXA_PCT_PADRAO,
    IDADES_ALVO_PADRAO,
    ParametrosBrody,
    Sexo,
    projetar,
)
from indexbeef_vision.virtual_box import montar_caixa_virtual
from indexbeef_vision.weight import K_PADRAO, estimar_de_medidas

VERSAO_PIPELINE: str = "0.1.0"


def ping() -> dict[str, str]:
    return {"status": "ok", "pipeline": VERSAO_PIPELINE}


def _com_conf(valor: float, confianca: float) -> dict[str, float]:
    return {"valor": valor, "confianca": confianca}


def montar_payload(
    *,
    avaliacao_id: str | UUID,
    kp_cm: Keypoints,
    sexo: Sexo,
    idade_meses: float,
    calibracao: Calibracao | None = None,
    largura_garupa_cm: float | None = None,
    area_tronco_cm2: float | None = None,
    largura_torax_cm: float | None = None,
    k_peso: float = K_PADRAO,
    params_projecao: ParametrosBrody | None = None,
    idades_alvo_meses: tuple[int, ...] = IDADES_ALVO_PADRAO,
    faixa_pct: float = FAIXA_PCT_PADRAO,
    confianca_keypoints: float = 1.0,
    frames_usados: int = 1,
    imagens: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Pipeline integrado: keypoints -> medidas -> caixa -> peso -> projecao.

    Retorna um dict pronto para persistencia em JSONB e para resposta HTTP.
    """
    medidas = medir(
        kp_cm,
        largura_garupa_cm=largura_garupa_cm,
        area_tronco_cm2=area_tronco_cm2,
        largura_torax_cm=largura_torax_cm,
    )
    caixa = montar_caixa_virtual(medidas)
    peso = estimar_de_medidas(medidas, k=k_peso)
    projecao = projetar(
        peso_atual_kg=peso.peso_kg,
        idade_atual_meses=idade_meses,
        sexo=sexo,
        params=params_projecao,
        idades_alvo_meses=idades_alvo_meses,
        faixa_pct=faixa_pct,
    )

    medidas_cm: dict[str, dict[str, float]] = {
        "altura_cernelha": _com_conf(medidas.altura_cernelha, confianca_keypoints),
        "altura_garupa": _com_conf(medidas.altura_garupa, confianca_keypoints),
        "comprimento_corporal": _com_conf(medidas.comprimento_corporal, confianca_keypoints),
        "profundidade_toracica": _com_conf(medidas.profundidade_toracica, confianca_keypoints),
        "comprimento_garupa": _com_conf(medidas.comprimento_garupa, confianca_keypoints),
        "altura_cupim": _com_conf(medidas.altura_cupim, confianca_keypoints),
        "umbigo_chao": _com_conf(medidas.umbigo_chao, confianca_keypoints),
    }
    if medidas.largura_garupa is not None:
        medidas_cm["largura_garupa"] = _com_conf(medidas.largura_garupa, confianca_keypoints)
    if medidas.perimetro_toracico_est is not None:
        medidas_cm["perimetro_toracico_est"] = _com_conf(
            medidas.perimetro_toracico_est, confianca_keypoints,
        )

    payload: dict[str, Any] = {
        "avaliacao_id": str(avaliacao_id),
        "versao_pipeline": VERSAO_PIPELINE,
        "frames_usados": frames_usados,
        "medidas_cm": medidas_cm,
        "angulos_graus": {
            "inclinacao_garupa": medidas.inclinacao_garupa,
            "jarrete": medidas.angulo_jarrete,
        },
        "caixa_virtual": {
            "C": caixa.c_cm,
            "P": caixa.p_cm,
            "L": caixa.l_cm,
            "volume_cm3": caixa.volume_cm3,
            "volume_l": caixa.volume_l,
            "ipl": caixa.ipl,
            "compacidade": caixa.compacidade,
            "indice_comprimento": caixa.indice_comprimento,
        },
        "peso": {
            "peso_kg": peso.peso_kg,
            "k": peso.k,
            "metodo": peso.metodo,
        },
        "projecao_peso": {
            "sexo": projecao.sexo,
            "metodo": projecao.metodo,
            "parametros_ajustados": {
                "peso_adulto_kg": projecao.parametros_ajustados.peso_adulto_kg,
                "B": projecao.parametros_ajustados.B,
                "k": projecao.parametros_ajustados.k,
            },
            "pontos": [
                {
                    "idade_meses": p.idade_meses,
                    "peso_kg": p.peso_kg,
                    "peso_min_kg": p.peso_min_kg,
                    "peso_max_kg": p.peso_max_kg,
                }
                for p in projecao.pontos
            ],
        },
    }
    if calibracao is not None and calibracao.placas:
        placa0 = calibracao.placas[0]
        payload["calibracao"] = {
            "px_por_cm": calibracao.px_por_cm,
            "erro_reproj_px": placa0.erro_reproj_px,
            "num_placas": len(calibracao.placas),
            "tamanho_placa_cm": calibracao.tamanho_placa_cm,
        }
    if imagens:
        payload["imagens"] = dict(imagens)
    return payload
