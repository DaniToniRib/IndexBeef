"""Testes do seletor de melhor frame por nitidez."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from indexbeef_vision.frames import FrameExtraido
from indexbeef_worker.frame_selector import nitidez_laplaciano, selecionar_melhor_frame


def _salvar_frame(destino: Path, nitido: bool) -> Path:
    """Cria um JPEG sintetico: nitido (bordas nítidas) ou desfocado (blur gaussiano)."""
    lado = 160
    img = np.zeros((lado, lado, 3), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (140, 140), (255, 255, 255), 2)
    cv2.line(img, (0, 80), (160, 80), (200, 200, 200), 1)
    if not nitido:
        img = cv2.GaussianBlur(img, (31, 31), 10)
    cv2.imwrite(str(destino), img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return destino


def test_nitidez_imagem_nitida_maior_que_desfocada(tmp_path: Path) -> None:
    p_nitido = _salvar_frame(tmp_path / "nitido.jpg", nitido=True)
    p_desfocado = _salvar_frame(tmp_path / "desfocado.jpg", nitido=False)
    assert nitidez_laplaciano(p_nitido) > nitidez_laplaciano(p_desfocado)


def test_nitidez_arquivo_inexistente_retorna_zero(tmp_path: Path) -> None:
    assert nitidez_laplaciano(tmp_path / "nao_existe.jpg") == 0.0


def test_selecionar_melhor_frame_lista_vazia() -> None:
    assert selecionar_melhor_frame([]) is None


def test_selecionar_melhor_frame_escolhe_nitido(tmp_path: Path) -> None:
    frames = []
    for i, nitido in enumerate([False, True, False]):
        arquivo = tmp_path / f"{i:04d}.jpg"
        _salvar_frame(arquivo, nitido=nitido)
        frames.append(FrameExtraido(indice=i, arquivo=arquivo, tempo_s=float(i)))

    melhor = selecionar_melhor_frame(frames)
    assert melhor is not None
    assert melhor.indice == 1  # o frame nitido esta no indice 1


def test_selecionar_melhor_frame_unico_elemento(tmp_path: Path) -> None:
    arquivo = tmp_path / "frame.jpg"
    _salvar_frame(arquivo, nitido=True)
    f = FrameExtraido(indice=0, arquivo=arquivo, tempo_s=0.0)
    assert selecionar_melhor_frame([f]) is f


def test_selecionar_melhor_frame_pipeline_completo(video_sintetico, tmp_path: Path) -> None:
    """Integra extrair_frames + selecionar_melhor_frame."""
    from indexbeef_vision.frames import extrair_frames

    video = video_sintetico(fps=30, n_frames=30)
    frames = extrair_frames(video, tmp_path / "frames", fps_alvo=5.0)
    assert len(frames) == 5
    melhor = selecionar_melhor_frame(frames)
    assert melhor is not None
    assert melhor.arquivo.exists()
