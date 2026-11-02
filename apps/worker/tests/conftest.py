from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from indexbeef_vision.calibration import DICIONARIO_PADRAO


def _escrever_video_sintetico(destino: Path, fps: int, n_frames: int, lado: int = 160) -> Path:
    """Escreve um mp4 sintetico (fundo escuro + retangulo claro movendo-se)."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw = cv2.VideoWriter(str(destino), fourcc, fps, (lado, lado))
    if not vw.isOpened():
        raise RuntimeError("VideoWriter nao abriu (codec mp4v indisponivel)")
    try:
        for i in range(n_frames):
            frame = np.full((lado, lado, 3), 20, dtype=np.uint8)
            x = int(10 + (lado - 60) * (i / max(1, n_frames - 1)))
            cv2.rectangle(frame, (x, 60), (x + 40, 110), (180, 180, 180), -1)
            vw.write(frame)
    finally:
        vw.release()
    return destino


def _gerar_marcador(aruco_id: int, lado_px: int) -> np.ndarray:
    dicio = cv2.aruco.getPredefinedDictionary(DICIONARIO_PADRAO)
    return cv2.aruco.generateImageMarker(dicio, aruco_id, lado_px)


def _imagem_com_placa(
    aruco_id: int,
    lado_marcador_px: int = 400,
    tamanho_imagem_px: int = 1000,
    posicao_tl_px: tuple[int, int] | None = None,
) -> np.ndarray:
    img = np.full((tamanho_imagem_px, tamanho_imagem_px), 255, dtype=np.uint8)
    marcador = _gerar_marcador(aruco_id, lado_marcador_px)
    if posicao_tl_px is None:
        c = (tamanho_imagem_px - lado_marcador_px) // 2
        posicao_tl_px = (c, c)
    x, y = posicao_tl_px
    img[y : y + lado_marcador_px, x : x + lado_marcador_px] = marcador
    return img


def _aplicar_perspectiva(imagem: np.ndarray, deformacao: float = 0.1) -> np.ndarray:
    h, w = imagem.shape[:2]
    src = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
    dst = np.array(
        [
            [0, h * deformacao],
            [w * (1 - deformacao), 0],
            [w, h * (1 - deformacao)],
            [w * deformacao, h],
        ],
        dtype=np.float32,
    )
    H = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(imagem, H, (w, h), borderValue=255)


@pytest.fixture
def imagem_com_placa():
    """Factory: `imagem_com_placa(aruco_id=0, lado_marcador_px=400)` → ndarray uint8."""
    return _imagem_com_placa


@pytest.fixture
def imagem_com_duas_placas():
    """Imagem com placas id 0 (esquerda) e id 1 (direita), 400 px cada, lado 1200."""

    def _criar(lado_marcador_px: int = 400, tamanho_imagem_px: int = 1200) -> np.ndarray:
        img = np.full((tamanho_imagem_px, tamanho_imagem_px), 255, dtype=np.uint8)
        y = (tamanho_imagem_px - lado_marcador_px) // 2
        x_esq = 50
        x_dir = tamanho_imagem_px - lado_marcador_px - 50
        img[y : y + lado_marcador_px, x_esq : x_esq + lado_marcador_px] = _gerar_marcador(
            0, lado_marcador_px,
        )
        img[y : y + lado_marcador_px, x_dir : x_dir + lado_marcador_px] = _gerar_marcador(
            1, lado_marcador_px,
        )
        return img

    return _criar


@pytest.fixture
def aplicar_perspectiva():
    return _aplicar_perspectiva


@pytest.fixture
def animal_sintetico() -> dict[int, tuple[float, float]]:
    """Animal esquematico com 18 keypoints em cm (sistema y-para-baixo).

    Projetado para dar numeros exatos nas medidas:
    chao em y=100, cernelha(3)y=20 -> AC=80; ilio(6)y=25 -> AG=75; PT=60; etc.
    """
    return {
        0: (10.0, 30.0),  # focinho (nao usado em medidas)
        1: (25.0, 25.0),  # nuca
        2: (55.0, 10.0),  # topo cupim
        3: (60.0, 20.0),  # cernelha
        4: (100.0, 25.0),  # meio dorso
        5: (120.0, 25.0),  # lombo
        6: (140.0, 25.0),  # ilio
        7: (180.0, 45.0),  # isquio
        8: (190.0, 30.0),  # insercao da cauda
        9: (50.0, 40.0),  # ponta espadua
        10: (80.0, 35.0),  # cilha superior
        11: (80.0, 95.0),  # cilha inferior
        12: (100.0, 85.0),  # umbigo
        13: (90.0, 90.0),  # ventre
        14: (35.0, 80.0),  # joelho anterior
        15: (30.0, 100.0),  # casco anterior
        16: (165.0, 80.0),  # jarrete
        17: (170.0, 100.0),  # casco posterior
    }


@pytest.fixture
def video_sintetico(tmp_path: Path):
    """Factory: `video_sintetico(fps=30, n_frames=60)` -> Path do mp4 temporario."""

    def _criar(fps: int = 30, n_frames: int = 60) -> Path:
        return _escrever_video_sintetico(tmp_path / f"sint_{fps}_{n_frames}.mp4", fps, n_frames)

    return _criar
