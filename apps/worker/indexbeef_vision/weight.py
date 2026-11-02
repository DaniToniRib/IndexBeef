"""Peso estimado a partir das medidas (ver docs/05-avaliacoes-e-indices.md, secao 1).

Fase 0 (atual): formula de referencia de fita de pesagem

    Peso (kg) ~= k * PT^2 * CC    (PT e CC em METROS)

Fase 1+ (futura): modelo treinado (LightGBM) com peso de balanca como alvo.
Meta: MAPE < 5% contra balanca.

**Importante**: o valor de `k` e literatura de fita de pesagem (zebuino).
Fita calibrada para taurino subestima o Nelore — o `k` DEVE ser recalibrado
contra a balanca durante o teste de campo no Pantanal (ver docs/08 Fase 2).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from indexbeef_vision.measurements import MedidasLineares

K_PADRAO: float = 90.0
METODO_FORMULA: str = "formula_pt_cc"


@dataclass(frozen=True)
class EstimativaPeso:
    """Resultado da estimativa de peso.

    Attributes
    ----------
    peso_kg : float
    k : float
        Coeficiente usado. Rastreado para que uma reavaliacao com `k` novo
        (apos recalibracao em campo) possa ser recalculada sem ambiguidade.
    metodo : str
        "formula_pt_cc" na Fase 0; "modelo_lightgbm_v1" quando o modelo chegar.
    """

    peso_kg: float
    k: float
    metodo: str = METODO_FORMULA


def peso_estimado(pt_cm: float, cc_cm: float, k: float = K_PADRAO) -> float:
    """Formula k * PT^2 * CC com conversao cm -> m. Retorna peso em kg."""
    if pt_cm <= 0 or cc_cm <= 0:
        raise ValueError(
            f"PT e CC precisam ser > 0 (pt_cm={pt_cm}, cc_cm={cc_cm})",
        )
    if k <= 0:
        raise ValueError(f"k precisa ser > 0 (k={k})")
    pt_m = pt_cm / 100.0
    cc_m = cc_cm / 100.0
    return k * pt_m * pt_m * cc_m


def estimar_de_medidas(
    medidas: MedidasLineares, k: float = K_PADRAO,
) -> EstimativaPeso:
    """Aplica a formula de peso usando PT e CC de `medidas`."""
    peso_kg = peso_estimado(
        medidas.profundidade_toracica, medidas.comprimento_corporal, k,
    )
    return EstimativaPeso(peso_kg=peso_kg, k=k, metodo=METODO_FORMULA)


def carregar_k_do_yaml(caminho: Path) -> float:
    """Le `peso.formula_pt_cc.k` de um arquivo YAML (config/indices.yaml)."""
    data = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    try:
        return float(data["peso"]["formula_pt_cc"]["k"])
    except (KeyError, TypeError) as e:
        raise ValueError(
            f"YAML sem chave peso.formula_pt_cc.k: {caminho}",
        ) from e
