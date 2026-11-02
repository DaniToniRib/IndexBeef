"""Deteccao + segmentacao da classe `cow` com YOLO-seg (ver docs/04, secao 2).

Fase 0: YOLO-seg pre-treinado no COCO (classe `cow` = 19). Em `Fase 1+` o
docs/04 preve refino via SAM 2 com a bbox como prompt e, mais tarde,
fine-tuning em Nelore (pelagem clara, cupim, barbela).

A funcao `_filtrar_resultado_yolo` e **pura** (recebe arrays, retorna dicts) e
e usada pelo wrapper `detectar_cows` que carrega o modelo. Isso segue a regra
do CLAUDE.md ("Funcoes do pipeline sao puras e testaveis, sem acessar o banco").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import cv2
import numpy as np

if TYPE_CHECKING:
    from ultralytics import YOLO

COCO_COW_CLASS_ID: int = 19
MODELO_PADRAO: str = "yolov8n-seg.pt"


@dataclass(frozen=True)
class DeteccaoCow:
    """Uma vaca detectada num frame.

    Attributes
    ----------
    bbox : tuple[int, int, int, int]
        (x1, y1, x2, y2) em pixels.
    mascara : np.ndarray
        Mascara binaria HxW (bool). Pode ser `None` em deteccoes sem mascara.
    confianca : float
        Score 0..1 do detector.
    """

    bbox: tuple[int, int, int, int]
    mascara: np.ndarray
    confianca: float

    @property
    def area_mascara_px(self) -> int:
        return int(self.mascara.sum())


class _ResultadoYolo(Protocol):
    """Protocolo minimo do objeto `Results` do Ultralytics que usamos.

    Permite tipar `_filtrar_resultado_yolo` sem forcar o import de ultralytics.
    """

    boxes: Any
    masks: Any


def _filtrar_resultado_yolo(
    resultado: _ResultadoYolo,
    tamanho_frame_hw: tuple[int, int],
    class_id: int = COCO_COW_CLASS_ID,
    confianca_minima: float = 0.25,
) -> list[DeteccaoCow]:
    """Filtra as deteccoes do YOLO, mantendo so a classe `cow`.

    Funcao pura: recebe o objeto Results do Ultralytics (ou um fake nos testes),
    retorna uma lista de DeteccaoCow.
    """
    boxes = resultado.boxes
    masks = resultado.masks
    if boxes is None or len(boxes) == 0:
        return []

    classes = np.asarray(boxes.cls).astype(int)
    confs = np.asarray(boxes.conf).astype(float)
    xyxy = np.asarray(boxes.xyxy).astype(float)

    mascaras_arr: np.ndarray | None = None
    if masks is not None and getattr(masks, "data", None) is not None:
        # `masks.data` tem shape (N, H', W') em float 0..1; redimensiona para o frame.
        mascaras_arr = np.asarray(masks.data)

    h, w = tamanho_frame_hw
    deteccoes: list[DeteccaoCow] = []
    for i, cls in enumerate(classes):
        if int(cls) != class_id:
            continue
        if float(confs[i]) < confianca_minima:
            continue
        x1, y1, x2, y2 = (int(v) for v in xyxy[i])
        if mascaras_arr is not None and i < len(mascaras_arr):
            m = mascaras_arr[i]
            if m.shape != (h, w):
                m = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
            mascara_bool = m.astype(bool)
        else:
            mascara_bool = np.zeros((h, w), dtype=bool)
            mascara_bool[max(0, y1) : max(0, y2), max(0, x1) : max(0, x2)] = True
        deteccoes.append(
            DeteccaoCow(
                bbox=(x1, y1, x2, y2),
                mascara=mascara_bool,
                confianca=float(confs[i]),
            ),
        )
    return deteccoes


def carregar_modelo(peso: str | Path = MODELO_PADRAO) -> YOLO:
    """Importa e carrega o modelo YOLO-seg. Requer `ultralytics` instalado.

    Em dev local: `pip install -e .[ml]` (ver pyproject do worker).
    """
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise RuntimeError(
            "ultralytics nao esta instalado. Instale o extra: pip install -e .[ml]",
        ) from e
    return YOLO(str(peso))


def detectar_cows(
    frame: np.ndarray,
    modelo: YOLO | None = None,
    confianca_minima: float = 0.25,
) -> list[DeteccaoCow]:
    """Detecta e segmenta vacas num frame BGR.

    Carrega `MODELO_PADRAO` se `modelo` for None. Util quando o worker roda
    como job unico; para processar vares frames, carregue o modelo uma vez e
    reutilize.
    """
    if modelo is None:
        modelo = carregar_modelo()
    resultados = modelo.predict(frame, verbose=False)
    if not resultados:
        return []
    h, w = frame.shape[:2]
    return _filtrar_resultado_yolo(resultados[0], (h, w), confianca_minima=confianca_minima)
