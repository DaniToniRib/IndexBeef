"""Testes de indexbeef_vision.weight (formula k * PT^2 * CC)."""

from __future__ import annotations

from pathlib import Path

import pytest

from indexbeef_vision.measurements import medir
from indexbeef_vision.weight import (
    K_PADRAO,
    METODO_FORMULA,
    EstimativaPeso,
    carregar_k_do_yaml,
    estimar_de_medidas,
    peso_estimado,
)


def test_peso_de_nelore_adulto_tipico() -> None:
    # Nelore novilha: PT ~180 cm, CC ~140 cm, k padrao 90
    # P = 90 * 1.80^2 * 1.40 = 90 * 3.24 * 1.40 = 408.24
    peso = peso_estimado(180.0, 140.0, K_PADRAO)
    assert peso == pytest.approx(408.24, abs=0.01)


def test_formula_eh_quadratica_no_pt_e_linear_no_cc() -> None:
    base = peso_estimado(100.0, 100.0, 100.0)
    # dobrar PT -> peso 4x; dobrar CC -> peso 2x
    assert peso_estimado(200.0, 100.0, 100.0) == pytest.approx(4 * base)
    assert peso_estimado(100.0, 200.0, 100.0) == pytest.approx(2 * base)


def test_k_padrao_vem_da_literatura_de_fita() -> None:
    # Nao mudar sem revalidar docs/05. Valor atual = 90.
    assert K_PADRAO == 90.0


@pytest.mark.parametrize(
    "pt, cc",
    [(0.0, 100.0), (-1.0, 100.0), (100.0, 0.0), (100.0, -5.0)],
)
def test_valores_nao_positivos_levantam(pt: float, cc: float) -> None:
    with pytest.raises(ValueError, match="precisam ser > 0"):
        peso_estimado(pt, cc)


def test_k_nao_positivo_levanta() -> None:
    with pytest.raises(ValueError, match=r"k precisa ser > 0"):
        peso_estimado(100.0, 100.0, 0.0)


def test_estimar_de_medidas_usa_pt_e_cc(animal_sintetico) -> None:
    medidas = medir(animal_sintetico)
    est = estimar_de_medidas(medidas)

    assert isinstance(est, EstimativaPeso)
    assert est.metodo == METODO_FORMULA
    assert est.k == K_PADRAO
    # Replica manual: PT=60 cm = 0.6 m, CC = sqrt(16925) cm ~ 1.301 m
    #                 P = 90 * 0.36 * 1.3009... ~ 42.15 kg
    assert est.peso_kg == pytest.approx(42.1491, abs=0.01)


def test_k_customizado_mudanca_proporcional(animal_sintetico) -> None:
    medidas = medir(animal_sintetico)
    base = estimar_de_medidas(medidas, k=90.0).peso_kg
    dobro = estimar_de_medidas(medidas, k=180.0).peso_kg
    assert dobro == pytest.approx(2 * base)


def test_carregar_k_do_yaml(tmp_path: Path) -> None:
    yml = tmp_path / "indices.yaml"
    yml.write_text(
        "peso:\n  formula_pt_cc:\n    k: 87.5\n",
        encoding="utf-8",
    )
    assert carregar_k_do_yaml(yml) == pytest.approx(87.5)


def test_carregar_k_do_yaml_do_repo() -> None:
    """Garante que o config/indices.yaml de verdade e carregavel."""
    repo = Path(__file__).resolve().parents[3]
    yml = repo / "config" / "indices.yaml"
    if not yml.exists():
        pytest.skip(f"config nao encontrado no repo: {yml}")
    k = carregar_k_do_yaml(yml)
    assert k > 0


def test_carregar_k_do_yaml_erro_se_falta_chave(tmp_path: Path) -> None:
    yml = tmp_path / "x.yaml"
    yml.write_text("peso: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="peso.formula_pt_cc.k"):
        carregar_k_do_yaml(yml)
