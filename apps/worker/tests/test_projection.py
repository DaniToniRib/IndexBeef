"""Testes de indexbeef_vision.projection (curva Brody)."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from indexbeef_vision.projection import (
    FAIXA_PCT_PADRAO,
    IDADES_ALVO_PADRAO,
    PARAMETROS_PADRAO,
    ParametrosBrody,
    ajustar_peso_adulto,
    carregar_faixa_pct,
    carregar_parametros_do_yaml,
    peso_brody,
    projetar,
)


def test_peso_brody_formula_direta() -> None:
    # W = A*(1 - B*exp(-k*t)). A=450, B=0.9, k=0.045, t=24
    # exp(-0.045*24) = exp(-1.08) ≈ 0.3396
    # W = 450 * (1 - 0.9 * 0.3396) = 450 * (1 - 0.3056) = 450 * 0.6944 ≈ 312.5
    p = ParametrosBrody(450.0, 0.9, 0.045)
    esperado = 450.0 * (1.0 - 0.9 * math.exp(-0.045 * 24))
    assert peso_brody(24, p) == pytest.approx(esperado)
    assert peso_brody(24, p) == pytest.approx(312.49, abs=0.5)


def test_peso_brody_tende_ao_adulto_quando_t_grande() -> None:
    p = ParametrosBrody(450.0, 0.9, 0.045)
    # t -> infinito, exp(-k*t) -> 0, W -> A
    assert peso_brody(1000, p) == pytest.approx(450.0, abs=0.1)


def test_peso_brody_cresce_monotonicamente() -> None:
    p = PARAMETROS_PADRAO["femea"]
    pesos = [peso_brody(t, p) for t in range(1, 60)]
    for anterior, atual in zip(pesos, pesos[1:], strict=False):
        assert atual > anterior


def test_peso_brody_rejeita_idade_negativa() -> None:
    with pytest.raises(ValueError, match="idade precisa ser >= 0"):
        peso_brody(-1, PARAMETROS_PADRAO["femea"])


def test_ajustar_peso_adulto_faz_curva_passar_pelo_ponto() -> None:
    base = PARAMETROS_PADRAO["femea"]
    ajustado = ajustar_peso_adulto(peso_atual_kg=200.0, idade_atual_meses=18, params=base)
    # Depois do ajuste, peso_brody(18, ajustado) == 200
    assert peso_brody(18, ajustado) == pytest.approx(200.0, abs=0.01)
    # B e k foram preservados
    assert ajustado.B == base.B
    assert ajustado.k == base.k


def test_ajustar_rejeita_valores_nao_positivos() -> None:
    base = PARAMETROS_PADRAO["femea"]
    with pytest.raises(ValueError, match="precisam ser > 0"):
        ajustar_peso_adulto(0.0, 18, base)
    with pytest.raises(ValueError, match="precisam ser > 0"):
        ajustar_peso_adulto(200.0, 0.0, base)


def test_projetar_gera_tres_pontos_padrao() -> None:
    projecao = projetar(peso_atual_kg=200.0, idade_atual_meses=18, sexo="femea")
    assert len(projecao.pontos) == 3
    assert tuple(p.idade_meses for p in projecao.pontos) == IDADES_ALVO_PADRAO


def test_projetar_passa_pelo_ponto_atual_na_idade_atual() -> None:
    # Ponto atual deve bater quando a idade atual coincide com um alvo
    projecao = projetar(
        peso_atual_kg=200.0,
        idade_atual_meses=18,
        sexo="femea",
        idades_alvo_meses=(18, 24, 30),
    )
    p18 = next(p for p in projecao.pontos if p.idade_meses == 18)
    assert p18.peso_kg == pytest.approx(200.0, abs=0.01)


def test_projetar_cresce_entre_18_e_30_meses() -> None:
    projecao = projetar(peso_atual_kg=200.0, idade_atual_meses=18, sexo="femea")
    pesos = [p.peso_kg for p in projecao.pontos]
    assert pesos == sorted(pesos)


def test_projetar_faixa_min_max_cerca_do_ponto() -> None:
    projecao = projetar(peso_atual_kg=250.0, idade_atual_meses=20, sexo="femea")
    for ponto in projecao.pontos:
        assert ponto.peso_min_kg < ponto.peso_kg < ponto.peso_max_kg
        # Faixa simetrica em percentual
        assert ponto.peso_min_kg == pytest.approx(ponto.peso_kg * (1 - FAIXA_PCT_PADRAO))
        assert ponto.peso_max_kg == pytest.approx(ponto.peso_kg * (1 + FAIXA_PCT_PADRAO))


def test_macho_usa_parametros_distintos_de_femea() -> None:
    # Mesmo peso/idade atual, macho projeta mais pesado (A maior na config padrao)
    pm = projetar(peso_atual_kg=250.0, idade_atual_meses=20, sexo="macho")
    pf = projetar(peso_atual_kg=250.0, idade_atual_meses=20, sexo="femea")
    peso_macho_30 = next(p.peso_kg for p in pm.pontos if p.idade_meses == 30)
    peso_femea_30 = next(p.peso_kg for p in pf.pontos if p.idade_meses == 30)
    assert peso_macho_30 > peso_femea_30


def test_projetar_rejeita_sexo_invalido() -> None:
    with pytest.raises(ValueError, match="sexo invalido"):
        projetar(peso_atual_kg=200.0, idade_atual_meses=18, sexo="M")  # type: ignore[arg-type]


def test_projetar_rejeita_faixa_negativa() -> None:
    with pytest.raises(ValueError, match="faixa_pct precisa ser >= 0"):
        projetar(peso_atual_kg=200.0, idade_atual_meses=18, sexo="femea", faixa_pct=-0.1)


def test_projetar_com_faixa_zero_min_igual_max() -> None:
    projecao = projetar(
        peso_atual_kg=200.0, idade_atual_meses=18, sexo="femea", faixa_pct=0.0,
    )
    for p in projecao.pontos:
        assert p.peso_min_kg == pytest.approx(p.peso_kg)
        assert p.peso_max_kg == pytest.approx(p.peso_kg)


def test_carregar_parametros_do_yaml_do_repo() -> None:
    repo = Path(__file__).resolve().parents[3]
    yml = repo / "config" / "indices.yaml"
    if not yml.exists():
        pytest.skip(f"config nao encontrado: {yml}")
    femea = carregar_parametros_do_yaml(yml, "femea")
    macho = carregar_parametros_do_yaml(yml, "macho")
    assert femea.peso_adulto_kg > 0 and femea.k > 0
    assert macho.peso_adulto_kg > femea.peso_adulto_kg
    assert carregar_faixa_pct(yml) > 0


def test_carregar_parametros_erro_se_falta_chave(tmp_path: Path) -> None:
    yml = tmp_path / "x.yaml"
    yml.write_text("projecao:\n  brody: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="projecao.brody.femea"):
        carregar_parametros_do_yaml(yml, "femea")


def test_carregar_faixa_pct_default_quando_ausente(tmp_path: Path) -> None:
    yml = tmp_path / "x.yaml"
    yml.write_text("projecao: {}\n", encoding="utf-8")
    assert carregar_faixa_pct(yml) == FAIXA_PCT_PADRAO
