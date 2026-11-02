"""Testes do pipeline unificado (montar_payload)."""

from __future__ import annotations

import math
from uuid import uuid4

import pytest

from indexbeef_vision.pipeline import VERSAO_PIPELINE, montar_payload


def test_payload_tem_chaves_obrigatorias(animal_sintetico) -> None:
    payload = montar_payload(
        avaliacao_id=uuid4(), kp_cm=animal_sintetico, sexo="femea", idade_meses=18,
    )
    for chave in (
        "avaliacao_id",
        "versao_pipeline",
        "frames_usados",
        "medidas_cm",
        "angulos_graus",
        "caixa_virtual",
        "peso",
        "projecao_peso",
    ):
        assert chave in payload, f"faltou {chave}"
    assert payload["versao_pipeline"] == VERSAO_PIPELINE


def test_medidas_tem_valor_e_confianca(animal_sintetico) -> None:
    payload = montar_payload(
        avaliacao_id="av-1",
        kp_cm=animal_sintetico,
        sexo="femea",
        idade_meses=18,
        confianca_keypoints=0.85,
    )
    for nome in (
        "altura_cernelha",
        "altura_garupa",
        "comprimento_corporal",
        "profundidade_toracica",
        "comprimento_garupa",
        "altura_cupim",
        "umbigo_chao",
    ):
        bloco = payload["medidas_cm"][nome]
        assert "valor" in bloco and "confianca" in bloco
        assert bloco["confianca"] == pytest.approx(0.85)


def test_valores_batem_com_animal_sintetico(animal_sintetico) -> None:
    payload = montar_payload(
        avaliacao_id="av-1", kp_cm=animal_sintetico, sexo="femea", idade_meses=18,
    )
    assert payload["medidas_cm"]["altura_cernelha"]["valor"] == pytest.approx(80.0)
    assert payload["medidas_cm"]["profundidade_toracica"]["valor"] == pytest.approx(60.0)
    assert payload["medidas_cm"]["comprimento_corporal"]["valor"] == pytest.approx(
        math.sqrt(16925),
    )
    assert payload["caixa_virtual"]["compacidade"] == pytest.approx(0.75)
    # IPL e L nao vieram -> permanecem None
    assert payload["caixa_virtual"]["ipl"] is None
    assert payload["caixa_virtual"]["L"] is None


def test_largura_garupa_popula_caixa_e_medidas(animal_sintetico) -> None:
    payload = montar_payload(
        avaliacao_id="av-1",
        kp_cm=animal_sintetico,
        sexo="femea",
        idade_meses=18,
        largura_garupa_cm=18.0,
    )
    assert payload["caixa_virtual"]["L"] == pytest.approx(18.0)
    assert payload["caixa_virtual"]["volume_l"] is not None
    assert "largura_garupa" in payload["medidas_cm"]


def test_bloco_peso_e_projecao(animal_sintetico) -> None:
    payload = montar_payload(
        avaliacao_id="av-1", kp_cm=animal_sintetico, sexo="femea", idade_meses=18,
    )
    assert payload["peso"]["metodo"] == "formula_pt_cc"
    assert payload["peso"]["peso_kg"] > 0
    assert payload["peso"]["k"] == 90.0
    pontos = payload["projecao_peso"]["pontos"]
    assert [p["idade_meses"] for p in pontos] == [18, 24, 30]
    assert pontos[0]["peso_kg"] < pontos[1]["peso_kg"] < pontos[2]["peso_kg"]
    for p in pontos:
        assert p["peso_min_kg"] < p["peso_kg"] < p["peso_max_kg"]


def test_bloco_calibracao_opcional(animal_sintetico, imagem_com_placa) -> None:
    from indexbeef_vision.calibration import calibrar

    img = imagem_com_placa(aruco_id=0, lado_marcador_px=400, tamanho_imagem_px=1000)
    calib = calibrar(img, tamanho_placa_cm=40.0)
    payload = montar_payload(
        avaliacao_id="av-1",
        kp_cm=animal_sintetico,
        sexo="femea",
        idade_meses=18,
        calibracao=calib,
    )
    assert "calibracao" in payload
    assert payload["calibracao"]["num_placas"] == 1
    assert payload["calibracao"]["tamanho_placa_cm"] == 40.0
    assert payload["calibracao"]["px_por_cm"] > 0


def test_sem_calibracao_nao_inclui_bloco(animal_sintetico) -> None:
    payload = montar_payload(
        avaliacao_id="av-1", kp_cm=animal_sintetico, sexo="femea", idade_meses=18,
    )
    assert "calibracao" not in payload


def test_imagens_opcional(animal_sintetico) -> None:
    payload = montar_payload(
        avaliacao_id="av-1",
        kp_cm=animal_sintetico,
        sexo="femea",
        idade_meses=18,
        imagens={"lateral_anotada": "s3://bucket/av1/lat.jpg"},
    )
    assert payload["imagens"] == {"lateral_anotada": "s3://bucket/av1/lat.jpg"}


def test_payload_e_serializavel_em_json(animal_sintetico) -> None:
    import json

    payload = montar_payload(
        avaliacao_id=uuid4(),
        kp_cm=animal_sintetico,
        sexo="femea",
        idade_meses=18,
        largura_garupa_cm=18.0,
    )
    # roundtrip
    s = json.dumps(payload)
    assert isinstance(s, str)
    recarregado = json.loads(s)
    assert recarregado["versao_pipeline"] == VERSAO_PIPELINE
