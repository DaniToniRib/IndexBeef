"""Medidas lineares a partir dos keypoints laterais (ver docs/04-pipeline-visao.md, secao 8).

As funcoes recebem os keypoints ja em centimetros (apos `calibration.pixel_para_cm`)
e sao **puras** — sem acesso a banco, filesystem ou modelo. Isso respeita a regra
do CLAUDE.md e permite testar com coordenadas sinteticas.

Sistema de coordenadas: igual ao da imagem — x cresce para a direita, **y cresce
para baixo**. Portanto a "altura fisica" de um ponto `p` em relacao ao chao vale
`chao_y - p.y`. O chao e a media dos cascos anterior (15) e posterior (17).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

PontoCm = tuple[float, float]
Keypoints = dict[int, PontoCm]

# IDs dos keypoints laterais usados aqui (ver docs/04, secao 6).
TOPO_CUPIM = 2
CERNELHA = 3
ILIO = 6
ISQUIO = 7
PONTA_ESPADUA = 9
CILHA_SUPERIOR = 10
CILHA_INFERIOR = 11
UMBIGO = 12
JARRETE = 16
CASCO_ANTERIOR = 15
CASCO_POSTERIOR = 17


@dataclass(frozen=True)
class MedidasLineares:
    """Medidas em cm (comprimentos) e graus (angulos). Ver docs/06.

    Campos opcionais exigem informacoes alem da vista lateral:
    - `largura_garupa`: vista traseira ou dorsal.
    - `area_tronco_cm2`: mascara de segmentacao (prompt futuro).
    - `perimetro_toracico_est`: elipse PT x largura do torax.
    """

    altura_cernelha: float
    altura_garupa: float
    comprimento_corporal: float
    profundidade_toracica: float
    comprimento_garupa: float
    inclinacao_garupa: float  # graus
    altura_cupim: float
    umbigo_chao: float
    angulo_jarrete: float  # graus
    largura_garupa: float | None = None
    area_tronco_cm2: float | None = None
    perimetro_toracico_est: float | None = None


def _dist(a: PontoCm, b: PontoCm) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _y(p: PontoCm) -> float:
    return p[1]


def chao_y(kp: Keypoints) -> float:
    """Linha do chao em cm — media dos y dos cascos 15 e 17."""
    return (_y(kp[CASCO_ANTERIOR]) + _y(kp[CASCO_POSTERIOR])) / 2.0


def altura_cernelha(kp: Keypoints) -> float:
    return chao_y(kp) - _y(kp[CERNELHA])


def altura_garupa(kp: Keypoints) -> float:
    return chao_y(kp) - _y(kp[ILIO])


def comprimento_corporal(kp: Keypoints) -> float:
    return _dist(kp[PONTA_ESPADUA], kp[ISQUIO])


def profundidade_toracica(kp: Keypoints) -> float:
    return _dist(kp[CILHA_SUPERIOR], kp[CILHA_INFERIOR])


def comprimento_garupa(kp: Keypoints) -> float:
    return _dist(kp[ILIO], kp[ISQUIO])


def inclinacao_garupa(kp: Keypoints) -> float:
    """Angulo (graus) da reta ilio -> isquio com a horizontal.

    Em coord-image (y para baixo), angulo positivo = garupa caida
    (isquio mais baixo que ilio).
    """
    dx = kp[ISQUIO][0] - kp[ILIO][0]
    dy = kp[ISQUIO][1] - kp[ILIO][1]
    return math.degrees(math.atan2(dy, dx))


def altura_cupim(kp: Keypoints) -> float:
    """Distancia vertical absoluta entre topo do cupim e cernelha."""
    return abs(_y(kp[CERNELHA]) - _y(kp[TOPO_CUPIM]))


def umbigo_chao(kp: Keypoints) -> float:
    return chao_y(kp) - _y(kp[UMBIGO])


def _angulo_entre_vetores(a: PontoCm, b: PontoCm, c: PontoCm) -> float:
    """Angulo em graus formado em B pelos segmentos B->A e B->C."""
    v1x, v1y = a[0] - b[0], a[1] - b[1]
    v2x, v2y = c[0] - b[0], c[1] - b[1]
    dot = v1x * v2x + v1y * v2y
    n1 = math.hypot(v1x, v1y)
    n2 = math.hypot(v2x, v2y)
    if n1 == 0 or n2 == 0:
        return 0.0
    cos_ang = max(-1.0, min(1.0, dot / (n1 * n2)))
    return math.degrees(math.acos(cos_ang))


def angulo_jarrete(kp: Keypoints) -> float:
    """Angulo em graus formado por ilio (6) - jarrete (16) - casco posterior (17)."""
    return _angulo_entre_vetores(kp[ILIO], kp[JARRETE], kp[CASCO_POSTERIOR])


def _perimetro_elipse(a: float, b: float) -> float:
    """Aproximacao de Ramanujan para o perimetro de uma elipse de semi-eixos a e b."""
    return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))


def perimetro_toracico_estimado(pt_cm: float, largura_torax_cm: float) -> float:
    """Perimetro da elipse formada pela profundidade toracica e largura do torax."""
    return _perimetro_elipse(pt_cm / 2.0, largura_torax_cm / 2.0)


def medir(
    kp: Keypoints,
    *,
    largura_garupa_cm: float | None = None,
    area_tronco_cm2: float | None = None,
    largura_torax_cm: float | None = None,
) -> MedidasLineares:
    """Calcula todas as medidas disponiveis a partir dos keypoints laterais.

    `largura_garupa_cm`, `area_tronco_cm2` e `largura_torax_cm` vem de fora da
    vista lateral (traseira/dorsal + mascara); quando nao informados, os campos
    correspondentes ficam `None`.
    """
    pt = profundidade_toracica(kp)
    pte: float | None = None
    if largura_torax_cm is not None:
        pte = perimetro_toracico_estimado(pt, largura_torax_cm)
    return MedidasLineares(
        altura_cernelha=altura_cernelha(kp),
        altura_garupa=altura_garupa(kp),
        comprimento_corporal=comprimento_corporal(kp),
        profundidade_toracica=pt,
        comprimento_garupa=comprimento_garupa(kp),
        inclinacao_garupa=inclinacao_garupa(kp),
        altura_cupim=altura_cupim(kp),
        umbigo_chao=umbigo_chao(kp),
        angulo_jarrete=angulo_jarrete(kp),
        largura_garupa=largura_garupa_cm,
        area_tronco_cm2=area_tronco_cm2,
        perimetro_toracico_est=pte,
    )
