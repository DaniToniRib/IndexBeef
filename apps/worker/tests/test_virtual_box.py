"""Testes de indexbeef_vision.virtual_box (ver docs/04, secao 10)."""

from __future__ import annotations

import pytest

from indexbeef_vision.measurements import medir
from indexbeef_vision.virtual_box import CaixaVirtual, montar_caixa_virtual


def test_caixa_sem_largura_tem_volume_none(animal_sintetico) -> None:
    medidas = medir(animal_sintetico)
    caixa = montar_caixa_virtual(medidas)

    assert isinstance(caixa, CaixaVirtual)
    assert caixa.c_cm == pytest.approx(medidas.comprimento_corporal)
    assert caixa.p_cm == pytest.approx(60.0)
    assert caixa.l_cm is None
    assert caixa.volume_cm3 is None
    assert caixa.volume_l is None
    assert caixa.ipl is None
    # compacidade = PT/AC = 60/80 = 0.75; comprimento = CC/AC
    assert caixa.compacidade == pytest.approx(0.75)
    assert caixa.indice_comprimento == pytest.approx(
        medidas.comprimento_corporal / medidas.altura_cernelha,
    )


def test_caixa_com_largura_calcula_volume(animal_sintetico) -> None:
    medidas = medir(animal_sintetico, largura_garupa_cm=18.0)
    caixa = montar_caixa_virtual(medidas)

    esperado_cm3 = medidas.comprimento_corporal * 60.0 * 18.0
    assert caixa.l_cm == pytest.approx(18.0)
    assert caixa.volume_cm3 == pytest.approx(esperado_cm3)
    assert caixa.volume_l == pytest.approx(esperado_cm3 / 1000.0)


def test_caixa_com_area_calcula_ipl(animal_sintetico) -> None:
    medidas = medir(animal_sintetico, area_tronco_cm2=5000.0)
    caixa = montar_caixa_virtual(medidas)
    denom = medidas.comprimento_corporal * medidas.profundidade_toracica
    assert caixa.ipl == pytest.approx(5000.0 / denom)
    # Para o animal sintetico, IPL fica abaixo de 1 (silhueta nao preenche
    # completamente a caixa C*P).
    assert 0.0 < caixa.ipl < 1.0


def test_ipl_proximo_de_um_quando_area_preenche_caixa(animal_sintetico) -> None:
    medidas = medir(animal_sintetico)
    area_cheia = medidas.comprimento_corporal * medidas.profundidade_toracica
    medidas_cheias = medir(animal_sintetico, area_tronco_cm2=area_cheia)
    caixa = montar_caixa_virtual(medidas_cheias)
    assert caixa.ipl == pytest.approx(1.0)


def test_ac_zero_nao_quebra(animal_sintetico) -> None:
    kp_sem_altura = dict(animal_sintetico)
    kp_sem_altura[3] = (60.0, 100.0)  # cernelha na mesma altura do chao
    medidas = medir(kp_sem_altura)
    caixa = montar_caixa_virtual(medidas)
    # compacidade e indice ficam 0 (fallback) em vez de dividir por zero
    assert caixa.compacidade == 0.0
    assert caixa.indice_comprimento == 0.0
