"""Testes de indexbeef_vision.measurements.

Usa a fixture `animal_sintetico` (conftest.py) — 18 keypoints com coordenadas
escolhidas para dar numeros exatos ou facilmente verificaveis a mao.
"""

from __future__ import annotations

import math

import pytest

from indexbeef_vision.measurements import (
    MedidasLineares,
    altura_cernelha,
    altura_cupim,
    altura_garupa,
    angulo_jarrete,
    chao_y,
    comprimento_corporal,
    comprimento_garupa,
    inclinacao_garupa,
    medir,
    perimetro_toracico_estimado,
    profundidade_toracica,
    umbigo_chao,
)


def test_chao_e_altura_cernelha(animal_sintetico) -> None:
    assert chao_y(animal_sintetico) == pytest.approx(100.0)
    # cernelha (3) em y=20 -> altura = 100 - 20 = 80
    assert altura_cernelha(animal_sintetico) == pytest.approx(80.0)


def test_altura_garupa(animal_sintetico) -> None:
    assert altura_garupa(animal_sintetico) == pytest.approx(75.0)


def test_altura_cupim(animal_sintetico) -> None:
    # |20 - 10| = 10
    assert altura_cupim(animal_sintetico) == pytest.approx(10.0)


def test_umbigo_chao(animal_sintetico) -> None:
    # 100 - 85 = 15
    assert umbigo_chao(animal_sintetico) == pytest.approx(15.0)


def test_comprimento_corporal(animal_sintetico) -> None:
    # (180-50, 45-40) -> sqrt(130^2 + 5^2) = sqrt(16925)
    assert comprimento_corporal(animal_sintetico) == pytest.approx(math.sqrt(16925))


def test_profundidade_toracica(animal_sintetico) -> None:
    assert profundidade_toracica(animal_sintetico) == pytest.approx(60.0)


def test_comprimento_garupa(animal_sintetico) -> None:
    # sqrt(40^2 + 20^2) = sqrt(2000)
    assert comprimento_garupa(animal_sintetico) == pytest.approx(math.sqrt(2000))


def test_inclinacao_garupa(animal_sintetico) -> None:
    # atan2(20, 40) = atan(0.5)
    esperado = math.degrees(math.atan2(20, 40))
    assert inclinacao_garupa(animal_sintetico) == pytest.approx(esperado)
    assert esperado == pytest.approx(26.5651, abs=0.01)


def test_angulo_jarrete(animal_sintetico) -> None:
    # ilio(140,25), jarrete(165,80), casco(170,100)
    # v1=(-25,-55), v2=(5,20), dot=-1225, |v1|=sqrt(3650), |v2|=sqrt(425)
    cos_ang = -1225.0 / (math.sqrt(3650) * math.sqrt(425))
    esperado = math.degrees(math.acos(cos_ang))
    assert angulo_jarrete(animal_sintetico) == pytest.approx(esperado)
    assert esperado == pytest.approx(169.64, abs=0.1)


def test_medir_producao_opcionais_none(animal_sintetico) -> None:
    m = medir(animal_sintetico)
    assert isinstance(m, MedidasLineares)
    assert m.altura_cernelha == pytest.approx(80.0)
    assert m.largura_garupa is None
    assert m.area_tronco_cm2 is None
    assert m.perimetro_toracico_est is None


def test_medir_com_largura_torax_calcula_perimetro(animal_sintetico) -> None:
    m = medir(animal_sintetico, largura_torax_cm=40.0)
    # a=PT/2=30, b=20 -> Ramanujan: pi*(150 - sqrt(110*90))
    esperado = math.pi * (150.0 - math.sqrt(110.0 * 90.0))
    assert m.perimetro_toracico_est == pytest.approx(esperado)


def test_perimetro_elipse_degenera_em_circulo() -> None:
    # a = b = r -> perimetro = 2*pi*r
    r = 30.0
    assert perimetro_toracico_estimado(2 * r, 2 * r) == pytest.approx(2 * math.pi * r)


def test_angulo_entre_vetores_colineares_eh_zero_ou_180() -> None:
    # Ponto A alinhado com B e C: angulo = 0 (A no sentido B->C) ou 180 (oposto)
    kp = {
        6: (0.0, 0.0),
        16: (10.0, 0.0),
        17: (20.0, 0.0),  # alinhado -> angulo entre 6-16-17 = 180
        15: (0.0, 0.0),  # dummy para chao
    }
    assert angulo_jarrete(kp) == pytest.approx(180.0)
