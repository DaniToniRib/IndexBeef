"""Testes do gerador da placa ArUco.

Rode com: `cd hardware && pip install -r requirements.txt && pytest`.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from hardware.gerar_placa_aruco import (
    DICIONARIO,
    gerar_imagem_marcador,
    gerar_pdf_a3,
    gerar_pdf_tamanho_real,
)


@pytest.mark.parametrize("aruco_id", [0, 1])
def test_imagem_marcador_shape_e_dtype(aruco_id: int) -> None:
    img = gerar_imagem_marcador(aruco_id, pixels_lado=200)
    assert img.shape == (200, 200)
    assert img.dtype == np.uint8
    assert img[0, 0] == 0 and img[-1, -1] == 0


def _com_quiet_zone(img: np.ndarray, borda_px: int = 50) -> np.ndarray:
    """Adiciona borda branca ao redor do marcador (quiet zone).

    O detector ArUco precisa de margem branca para localizar os cantos; no PDF
    isso vem de `margem_cm`, mas na imagem bruta do `generateImageMarker` nao.
    """
    h, w = img.shape
    canvas_ = np.full((h + 2 * borda_px, w + 2 * borda_px), 255, dtype=np.uint8)
    canvas_[borda_px : borda_px + h, borda_px : borda_px + w] = img
    return canvas_


@pytest.mark.parametrize("aruco_id", [0, 1])
def test_marcador_eh_detectavel(aruco_id: int) -> None:
    img = _com_quiet_zone(gerar_imagem_marcador(aruco_id, pixels_lado=400))
    dicio = cv2.aruco.getPredefinedDictionary(DICIONARIO)
    detector = cv2.aruco.ArucoDetector(dicio)
    _, ids, _ = detector.detectMarkers(img)
    assert ids is not None, "nenhum marcador detectado"
    assert aruco_id in ids.flatten()


def test_pdf_tamanho_real_gera_arquivo(tmp_path: Path) -> None:
    saida = tmp_path / "placa.pdf"
    resultado = gerar_pdf_tamanho_real(
        aruco_id=0, saida=saida, tamanho_cm=40.0, margem_cm=2.0, pixels_lado=400,
    )
    assert resultado == saida
    assert saida.exists()
    assert saida.stat().st_size > 1000  # PDF nao-vazio
    # cabecalho PDF
    assert saida.read_bytes().startswith(b"%PDF-")


def test_pdf_a3_gera_arquivo(tmp_path: Path) -> None:
    saida = tmp_path / "placa-a3.pdf"
    resultado = gerar_pdf_a3(
        aruco_id=1, saida=saida, tamanho_cm_logico=40.0, pixels_lado=400,
    )
    assert resultado == saida
    assert saida.exists()
    assert saida.read_bytes().startswith(b"%PDF-")
