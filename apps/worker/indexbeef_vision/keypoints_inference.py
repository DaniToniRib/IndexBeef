"""Inferencia de keypoints anatomicos via YOLO-pose (Fase 1+ do docs/04).

Usa o modelo em MODELO_KEYPOINTS_PATH se existir; caso contrario retorna None
e o sistema cai para o modo manual/semiautomatico.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ultralytics import YOLO

MODELO_KEYPOINTS_PATH: str = os.getenv("INDEXBEEF_KEYPOINTS_MODEL", "")
NUM_KEYPOINTS = 18


@dataclass(frozen=True)
class KeypointPredito:
    id: int          # 0..17
    x: float         # pixels
    y: float         # pixels
    confianca: float  # 0..1


def carregar_modelo_keypoints(caminho: str | Path | None = None) -> YOLO | None:
    """Retorna modelo YOLO-pose ou None se nao encontrado."""
    caminho = caminho or MODELO_KEYPOINTS_PATH
    if not caminho or not Path(str(caminho)).exists():
        return None
    try:
        from ultralytics import YOLO
        return YOLO(str(caminho))
    except Exception:
        return None


def predizer_keypoints(
    frame: np.ndarray,
    modelo: YOLO | None,
    confianca_minima: float = 0.3,
) -> list[KeypointPredito] | None:
    """Retorna lista de keypoints preditos ou None se modelo indisponivel.

    Apenas keypoints com confianca >= confianca_minima sao incluidos.
    Retorna None se o modelo for None, se nao houver deteccoes, ou se o numero
    de keypoints retornado pelo modelo nao for NUM_KEYPOINTS.
    """
    if modelo is None:
        return None
    try:
        resultados = modelo.predict(frame, verbose=False)
        if not resultados or resultados[0].keypoints is None:
            return None
        kpts = resultados[0].keypoints
        if kpts.xy is None or len(kpts.xy) == 0:
            return None
        # take first detection (highest confidence animal)
        xy = kpts.xy[0].cpu().numpy()  # shape (NUM_KEYPOINTS, 2)
        conf = kpts.conf[0].cpu().numpy() if kpts.conf is not None else np.ones(len(xy))
        if len(xy) != NUM_KEYPOINTS:
            return None
        return [
            KeypointPredito(id=i, x=float(xy[i, 0]), y=float(xy[i, 1]), confianca=float(conf[i]))
            for i in range(NUM_KEYPOINTS)
            if float(conf[i]) >= confianca_minima
        ]
    except Exception:
        return None
