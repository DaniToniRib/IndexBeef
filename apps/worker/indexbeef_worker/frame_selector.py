"""Selecao do melhor frame de um video por nitidez (variancia do Laplaciano).

Referencia: Pertuz et al. (2013), Analysis of focus measure operators for
shape-from-focus. A variancia do Laplaciano e o operador mais simples e
eficaz para imagens de corpo inteiro tiradas com camera fixa.
"""

from __future__ import annotations

import cv2

from indexbeef_vision.frames import FrameExtraido


def nitidez_laplaciano(caminho) -> float:
    """Calcula a variancia do Laplaciano de uma imagem (quanto maior, mais nitida)."""
    img = cv2.imread(str(caminho))
    if img is None:
        return 0.0
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(cinza, cv2.CV_64F).var())


def selecionar_melhor_frame(
    frames: list[FrameExtraido],
) -> FrameExtraido | None:
    """Retorna o frame com maior nitidez, ou None se a lista estiver vazia."""
    if not frames:
        return None
    return max(frames, key=lambda f: nitidez_laplaciano(f.arquivo))
