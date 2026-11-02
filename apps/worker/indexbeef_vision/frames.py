"""Extracao de frames de video (ver docs/04-pipeline-visao.md, secao 1).

Usamos cv2.VideoCapture em vez de chamar ffmpeg direto para nao depender do
binario no PATH em dev. Em producao o Dockerfile do worker ja inclui ffmpeg
para outros cenarios (streams, formatos exoticos).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class FrameExtraido:
    indice: int
    arquivo: Path
    tempo_s: float


def _calcular_passo(fps_video: float, fps_alvo: float) -> int:
    if fps_video <= 0:
        raise ValueError("fps_video precisa ser > 0 (video invalido ou sem metadados)")
    if fps_alvo <= 0:
        raise ValueError("fps_alvo precisa ser > 0")
    passo = max(1, int(round(fps_video / fps_alvo)))
    return passo


def extrair_frames(
    video: Path,
    destino: Path,
    fps_alvo: float = 5.0,
    qualidade_jpeg: int = 90,
) -> list[FrameExtraido]:
    """Extrai frames do video em `fps_alvo` quadros por segundo.

    Parametros
    ----------
    video : Path
        Caminho do video (mp4, mov, avi).
    destino : Path
        Diretorio onde os JPGs serao salvos. Criado se nao existir.
    fps_alvo : float
        Quantos frames por segundo manter. O passo real sera
        `round(fps_video / fps_alvo)`, limitado a >= 1.
    qualidade_jpeg : int
        Qualidade JPEG (0-100). Default 90.

    Retorna
    -------
    list[FrameExtraido]
        Metadados dos frames escritos.
    """
    video = Path(video)
    destino = Path(destino)
    if not video.exists():
        raise FileNotFoundError(f"video nao encontrado: {video}")
    destino.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"nao foi possivel abrir o video: {video}")

    try:
        fps_video = cap.get(cv2.CAP_PROP_FPS) or 0.0
        passo = _calcular_passo(fps_video, fps_alvo)

        resultado: list[FrameExtraido] = []
        indice_lido = 0
        indice_salvo = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if indice_lido % passo == 0:
                tempo_s = indice_lido / fps_video if fps_video else 0.0
                nome = destino / f"{indice_salvo:04d}.jpg"
                cv2.imwrite(
                    str(nome), frame, [int(cv2.IMWRITE_JPEG_QUALITY), qualidade_jpeg],
                )
                resultado.append(
                    FrameExtraido(indice=indice_salvo, arquivo=nome, tempo_s=tempo_s),
                )
                indice_salvo += 1
            indice_lido += 1
        return resultado
    finally:
        cap.release()


def carregar_frame(caminho: Path) -> np.ndarray:
    """Le um frame como ndarray BGR."""
    img = cv2.imread(str(caminho))
    if img is None:
        raise RuntimeError(f"nao foi possivel ler o frame: {caminho}")
    return img
