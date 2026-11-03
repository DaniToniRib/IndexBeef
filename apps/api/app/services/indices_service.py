"""Servico de calculo de indices de aptidao, frame score, EPMURAS, GMD e projecao de peso.

Todas as funcoes sao puras: recebem dicts/primitivos e retornam dicts/floats.
Sem acesso a banco de dados.
"""

from __future__ import annotations

import math
from datetime import date
from pathlib import Path
from typing import Any

import yaml

_CFG_PATH = Path(__file__).resolve().parents[4] / "config" / "indices.yaml"


def _cfg() -> dict:
    with open(_CFG_PATH) as f:
        return yaml.safe_load(f)


def calcular_frame_score(
    altura_garupa_cm: float,
    sexo: str,
    nascimento: date,
    data: date,
) -> float | None:
    idade_meses = (data - nascimento).days / 30.44
    if idade_meses < 1:
        return None
    if sexo.upper() == "M":
        esperado_cm = 88.0 + 0.58 * min(idade_meses, 36)
        escala = 4.2
    else:
        esperado_cm = 84.0 + 0.50 * min(idade_meses, 36)
        escala = 3.8
    frame = 5.0 + (altura_garupa_cm - esperado_cm) / escala  # TODO: validar com zootecnista
    frame = max(1.0, min(9.0, frame))
    return round(frame, 1)


def sugerir_epmuras(medidas: dict, caixa_virtual: dict) -> dict[str, int | None]:
    # TODO: validar com zootecnista — valores hipoteticos
    result: dict[str, int | None] = {
        "E": None, "P": None, "M": None, "U": None, "R": None, "A": None, "S": None,
    }

    volume_l = caixa_virtual.get("volume_l")
    if volume_l is not None:
        v = float(volume_l)
        if v < 100:
            result["E"] = 1
        elif v < 150:
            result["E"] = 2
        elif v < 200:
            result["E"] = 3
        elif v < 250:
            result["E"] = 4
        elif v < 300:
            result["E"] = 5
        else:
            result["E"] = 6

    compacidade = caixa_virtual.get("compacidade")
    if compacidade is not None:
        c = float(compacidade)
        if c >= 1.20:
            result["P"] = 5
        elif c >= 1.10:
            result["P"] = 4
        elif c >= 1.00:
            result["P"] = 3
        elif c >= 0.90:
            result["P"] = 2
        elif c >= 0.80:
            result["P"] = 1

    lg = medidas.get("largura_garupa_cm")
    cc = medidas.get("comprimento_corporal_cm")
    if lg is not None and cc is not None and float(cc) > 0:
        ratio = float(lg) / float(cc)
        if ratio >= 0.30:
            result["M"] = 5
        elif ratio >= 0.27:
            result["M"] = 4
        elif ratio >= 0.24:
            result["M"] = 3
        elif ratio >= 0.21:
            result["M"] = 2
        else:
            result["M"] = 1

    umbigo = medidas.get("umbigo_chao_cm")
    cernelha = medidas.get("altura_cernelha_cm")
    if umbigo is not None and cernelha is not None and float(cernelha) > 0:
        ratio_u = float(umbigo) / float(cernelha)
        if ratio_u >= 0.20:
            result["U"] = 5
        elif ratio_u >= 0.15:
            result["U"] = 4
        elif ratio_u >= 0.12:
            result["U"] = 3
        elif ratio_u >= 0.09:
            result["U"] = 2
        else:
            result["U"] = 1

    return result


def calcular_gmd(pesagens: list[dict]) -> float | None:
    if len(pesagens) < 2:
        return None
    p0 = pesagens[0]
    p1 = pesagens[-1]
    dias = (p1["data"] - p0["data"]).days
    if dias == 0:
        return None
    return (float(p1["peso_kg"]) - float(p0["peso_kg"])) / dias


def calcular_projecao_brody(
    peso_atual_kg: float,
    sexo: str,
    idade_atual_meses: float,
    frame_score: float | None,
    cfg: dict,
) -> list[dict]:
    brody = cfg["projecao"]["brody"]
    sexo_key = "macho" if sexo.upper() == "M" else "femea"
    params = brody[sexo_key]
    A = float(params["peso_adulto_kg"])
    B = float(params["B"])
    k = float(params["k"])

    if frame_score is not None:
        A_ajustado = A * (1 + (frame_score - 5) * 0.03)
    else:
        A_ajustado = A

    faixa_pct = float(cfg["projecao"]["faixa_pct"])
    idades_alvo: list[int] = cfg["projecao"]["idades_alvo_meses"]

    W_atual_teorico = A_ajustado * (1 - B * math.exp(-k * idade_atual_meses))

    result = []
    for idade_alvo in idades_alvo:
        if idade_atual_meses >= idade_alvo:
            continue
        W_t = A_ajustado * (1 - B * math.exp(-k * idade_alvo))
        if W_atual_teorico > 0:
            W_projetado = W_t * (peso_atual_kg / W_atual_teorico)
        else:
            W_projetado = W_t
        result.append({
            "idade_meses": idade_alvo,
            "peso_kg": round(W_projetado, 1),
            "peso_min_kg": round(W_projetado * (1 - faixa_pct), 1),
            "peso_max_kg": round(W_projetado * (1 + faixa_pct), 1),
        })
    return result


def _normalizar_percentil(valores: list[float], valor: float) -> float:
    return sum(1 for v in valores if v < valor) / max(len(valores), 1) * 100


def calcular_indice(
    tipo: str,
    componentes_brutos: dict[str, float | None],
    grupo: list[float],
    cfg: dict,
) -> tuple[float, list[dict]]:
    pesos: dict[str, float] = cfg[f"indice_{tipo}"]["componentes"]
    contribuicoes: list[tuple[str, float]] = []
    soma_pesos = 0.0
    soma_ponderada = 0.0

    for nome, peso in pesos.items():
        if peso <= 0:
            continue
        valor = componentes_brutos.get(nome)
        if valor is None:
            contribuicao = 0.0
        else:
            contribuicao = peso * float(valor)
        soma_ponderada += contribuicao
        soma_pesos += peso
        contribuicoes.append((nome, abs(contribuicao)))

    indice_bruto = soma_ponderada * 100.0

    contribuicoes_sorted = sorted(contribuicoes, key=lambda x: x[1], reverse=True)
    soma_abs = sum(c for _, c in contribuicoes_sorted) or 1.0
    explicacao = [
        {
            "componente": nome,
            "contribuicao_pct": round(contrib / soma_abs * 100, 1),
        }
        for nome, contrib in contribuicoes_sorted[:3]
    ]

    return (round(indice_bruto, 2), explicacao)


def montar_componentes_garrote(
    medidas: dict,
    caixa: dict,
    escore: dict,
    gmd: float | None,
    deps: dict | None,
    peso_atual_kg: float | None,
    nascimento: date | None,
    data: date | None,
) -> dict[str, Any]:
    def _safe(v: Any, divisor: float) -> float | None:
        if v is None:
            return None
        return min(float(v) / divisor, 1.0)

    ipl = caixa.get("ipl")
    compacidade = caixa.get("compacidade")
    cc_cm = medidas.get("comprimento_corporal_cm")
    ac_cm = medidas.get("altura_cernelha_cm")
    lg_cm = medidas.get("largura_garupa_cm")

    comp_rel: float | None = None
    if cc_cm is not None and ac_cm is not None and float(ac_cm) > 0:
        comp_rel = min(float(cc_cm) / float(ac_cm) / 1.4, 1.0)

    m_val = escore.get("m_final") or escore.get("m_sugerido")

    gmd_norm: float | None = None
    if gmd is not None and peso_atual_kg and nascimento and data:
        gmd_norm = min(gmd / 1.0, 1.0)

    deps_norm: float | None = None
    if deps is not None:
        p450 = deps.get("P450")
        if p450 is not None:
            deps_norm = max(0.0, min(float(p450) / 150.0, 1.0))

    return {
        "ipl": _safe(ipl, 2.5),
        "compacidade_pt_ac": _safe(compacidade, 1.4),
        "comprimento_relativo": comp_rel,
        "largura_garupa": _safe(lg_cm, 60.0),
        "musculosidade_m": _safe(m_val, 6.0),
        "gmd_peso_idade": gmd_norm,
        "deps_crescimento_carcaca": deps_norm,
    }


def montar_componentes_reprodutor(
    medidas: dict,
    caixa: dict,
    escore: dict,
    deps: dict | None,
    exame_andrologico: dict | None,
) -> dict[str, Any]:
    def _safe(v: Any, divisor: float) -> float | None:
        if v is None:
            return None
        return min(float(v) / divisor, 1.0)

    e_val = escore.get("e_final") or escore.get("e_sugerido")
    p_val = escore.get("p_final") or escore.get("p_sugerido")
    a_val = escore.get("a_final") or escore.get("a_sugerido")
    u_val = escore.get("u_final") or escore.get("u_sugerido")
    r_val = escore.get("r_final") or escore.get("r_sugerido")
    s_val = escore.get("s_final") or escore.get("s_sugerido")

    ep: float | None = None
    vals_ep = [v for v in [_safe(e_val, 6.0), _safe(p_val, 6.0)] if v is not None]
    if vals_ep:
        ep = sum(vals_ep) / len(vals_ep)

    rs: float | None = None
    vals_rs = [v for v in [_safe(r_val, 6.0), _safe(s_val, 6.0)] if v is not None]
    if vals_rs:
        rs = sum(vals_rs) / len(vals_rs)

    pe_cm: float | None = None
    if exame_andrologico is not None:
        pe_raw = exame_andrologico.get("perimetro_escrotal_cm")
        if pe_raw is not None:
            pe_cm = min(float(pe_raw) / 40.0, 1.0)

    deps_norm: float | None = None
    if deps is not None:
        vals = []
        pe_dep = deps.get("PE")
        ipp_dep = deps.get("IPP")
        if pe_dep is not None:
            vals.append(max(0.0, min(float(pe_dep) / 25.0, 1.0)))
        if ipp_dep is not None:
            vals.append(max(0.0, min(float(ipp_dep) / 5.0, 1.0)))
        if vals:
            deps_norm = sum(vals) / len(vals)

    return {
        "estrutura_precocidade_ep": ep,
        "aprumos_a": _safe(a_val, 6.0),
        "umbigo_bainha_u": _safe(u_val, 6.0),
        "racial_sexualidade_rs": rs,
        "perimetro_escrotal_ajustado": pe_cm,
        "deps": deps_norm,
    }


def montar_componentes_matriz(
    medidas: dict,
    caixa: dict,
    escore: dict,
    deps: dict | None,
) -> dict[str, Any]:
    def _safe(v: Any, divisor: float) -> float | None:
        if v is None:
            return None
        return min(float(v) / divisor, 1.0)

    ipl = caixa.get("ipl")
    compacidade = caixa.get("compacidade")
    volume_l = caixa.get("volume_l")

    cap_vals = [v for v in [_safe(ipl, 2.5), _safe(compacidade, 1.4), _safe(volume_l, 400.0)] if v is not None]
    capacidade: float | None = sum(cap_vals) / len(cap_vals) if cap_vals else None

    lg_cm = medidas.get("largura_garupa_cm")
    cg_cm = medidas.get("comprimento_garupa_cm")
    garupa_vals = [v for v in [_safe(lg_cm, 55.0), _safe(cg_cm, 55.0)] if v is not None]
    garupa: float | None = sum(garupa_vals) / len(garupa_vals) if garupa_vals else None

    inclinacao: float | None = None
    graus = medidas.get("inclinacao_garupa_graus")
    if graus is not None:
        score_inc = (8.0 - abs(float(graus) - 5.5)) / 4.5
        inclinacao = max(0.0, min(score_inc, 1.0))

    a_val = escore.get("a_final") or escore.get("a_sugerido")
    u_val = escore.get("u_final") or escore.get("u_sugerido")
    r_val = escore.get("r_final") or escore.get("r_sugerido")
    s_val = escore.get("s_final") or escore.get("s_sugerido")

    fem_vals = [v for v in [_safe(r_val, 6.0), _safe(s_val, 6.0)] if v is not None]
    feminilidade: float | None = sum(fem_vals) / len(fem_vals) if fem_vals else None

    ecc_val = escore.get("ecc_final") or escore.get("ecc_sugerido")
    ecc_score: float | None = None
    if ecc_val is not None:
        ecc_score = max(0.0, min(1.0 - abs(float(ecc_val) - 5.5) / 2.0, 1.0))

    deps_norm: float | None = None
    if deps is not None:
        vals = []
        stay = deps.get("STAY")
        ipp = deps.get("IPP")
        if stay is not None:
            vals.append(max(0.0, min(float(stay) / 35.0, 1.0)))
        if ipp is not None:
            vals.append(max(0.0, min(float(ipp) / 5.0, 1.0)))
        if vals:
            deps_norm = sum(vals) / len(vals)

    return {
        "capacidade_corporal": capacidade,
        "garupa_lg_cg": garupa,
        "inclinacao_garupa_faixa": inclinacao,
        "aprumos_a": _safe(a_val, 6.0),
        "umbigo_u": _safe(u_val, 6.0),
        "feminilidade_rs": feminilidade,
        "ecc_adequado": ecc_score,
        "deps_maternas": deps_norm,
    }
