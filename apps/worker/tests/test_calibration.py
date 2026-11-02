"""Testes de indexbeef_vision.calibration (ver docs/04-pipeline-visao.md, secao 7)."""

from __future__ import annotations

import numpy as np
import pytest

from indexbeef_vision.calibration import (
    Calibracao,
    CalibracaoPlaca,
    NenhumaPlacaDetectada,
    calibrar,
    detectar_placas,
)


def test_detecta_uma_placa(imagem_com_placa) -> None:
    img = imagem_com_placa(aruco_id=0, lado_marcador_px=400, tamanho_imagem_px=1000)
    calib = calibrar(img, tamanho_placa_cm=40.0)

    assert isinstance(calib, Calibracao)
    assert len(calib.placas) == 1
    placa = calib.placas[0]
    assert isinstance(placa, CalibracaoPlaca)
    assert placa.aruco_id == 0
    assert placa.homografia.shape == (3, 3)
    # marcador de 400 px → 10 px/cm (placa de 40 cm).
    assert placa.px_por_cm == pytest.approx(10.0, abs=0.1)
    # Com 4 cantos exatos a reconstrucao e quase perfeita.
    assert placa.erro_reproj_px < 1e-3


def test_pixel_para_cm_recupera_cantos(imagem_com_placa) -> None:
    img = imagem_com_placa(aruco_id=0, lado_marcador_px=400, tamanho_imagem_px=1000)
    calib = calibrar(img, tamanho_placa_cm=40.0)
    placa = calib.placas[0]

    # Canto TL → (0, 0)
    cm_tl = calib.pixel_para_cm(tuple(placa.cantos_px[0]))
    assert cm_tl == pytest.approx((0.0, 0.0), abs=0.01)
    # Canto TR → (40, 0)
    cm_tr = calib.pixel_para_cm(tuple(placa.cantos_px[1]))
    assert cm_tr == pytest.approx((40.0, 0.0), abs=0.01)
    # Canto BR → (40, 40)
    cm_br = calib.pixel_para_cm(tuple(placa.cantos_px[2]))
    assert cm_br == pytest.approx((40.0, 40.0), abs=0.01)
    # Canto BL → (0, 40)
    cm_bl = calib.pixel_para_cm(tuple(placa.cantos_px[3]))
    assert cm_bl == pytest.approx((0.0, 40.0), abs=0.01)


def test_centro_da_placa_eh_metade_do_lado(imagem_com_placa) -> None:
    img = imagem_com_placa(aruco_id=0, lado_marcador_px=400, tamanho_imagem_px=1000)
    calib = calibrar(img, tamanho_placa_cm=40.0)
    placa = calib.placas[0]
    centro_px = placa.cantos_px.mean(axis=0)
    cm = calib.pixel_para_cm(tuple(centro_px))
    assert cm == pytest.approx((20.0, 20.0), abs=0.05)


def test_duas_placas_sao_detectadas(imagem_com_duas_placas) -> None:
    img = imagem_com_duas_placas(lado_marcador_px=400, tamanho_imagem_px=1200)
    calib = calibrar(img, tamanho_placa_cm=40.0)

    assert len(calib.placas) == 2
    ids = {p.aruco_id for p in calib.placas}
    assert ids == {0, 1}
    # px_por_cm medio e proximo de 10 (ambas sao 400 px / 40 cm).
    assert calib.px_por_cm == pytest.approx(10.0, abs=0.1)


def test_sem_placa_levanta(imagem_com_placa) -> None:
    img = np.full((500, 500), 128, dtype=np.uint8)
    with pytest.raises(NenhumaPlacaDetectada):
        calibrar(img, tamanho_placa_cm=40.0)


def test_funciona_sob_perspectiva(imagem_com_placa, aplicar_perspectiva) -> None:
    img = imagem_com_placa(aruco_id=0, lado_marcador_px=400, tamanho_imagem_px=1000)
    img_warp = aplicar_perspectiva(img, deformacao=0.12)

    calib = calibrar(img_warp, tamanho_placa_cm=40.0)
    placa = calib.placas[0]

    # Com perspectiva a placa aparece deformada → px_por_cm medio diverge de 10,
    # mas a homografia continua recuperando as coordenadas corretas dos cantos.
    cm_tl = calib.pixel_para_cm(tuple(placa.cantos_px[0]))
    cm_br = calib.pixel_para_cm(tuple(placa.cantos_px[2]))
    assert cm_tl == pytest.approx((0.0, 0.0), abs=0.1)
    assert cm_br == pytest.approx((40.0, 40.0), abs=0.1)
    assert placa.erro_reproj_px < 1e-2


def test_detectar_placas_retorna_lista_vazia_sem_marcador() -> None:
    img = np.full((300, 300), 200, dtype=np.uint8)
    assert detectar_placas(img) == []
