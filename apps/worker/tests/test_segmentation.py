"""Testes de indexbeef_vision.segmentation.

- A funcao pura `_filtrar_resultado_yolo` e testada com objetos fake.
- O teste de integracao real (`test_detectar_cows_com_yolo`) e marcado com
  `@pytest.mark.ml` e so roda quando ultralytics estiver instalado.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from indexbeef_vision.segmentation import (
    COCO_COW_CLASS_ID,
    DeteccaoCow,
    _filtrar_resultado_yolo,
)


class _FakeBoxes:
    """Simula o objeto `Results.boxes` do Ultralytics (atributos cls/conf/xyxy + len)."""

    def __init__(
        self, classes: list[int], confs: list[float], xyxy: list[list[float]],
    ) -> None:
        self.cls = np.asarray(classes)
        self.conf = np.asarray(confs)
        self.xyxy = np.asarray(xyxy, dtype=float).reshape(-1, 4)

    def __len__(self) -> int:
        return len(self.cls)


def test_filtra_apenas_classe_cow() -> None:
    boxes = _FakeBoxes(
        classes=[0, COCO_COW_CLASS_ID, 2, COCO_COW_CLASS_ID],
        confs=[0.9, 0.85, 0.95, 0.3],
        xyxy=[[0, 0, 10, 10], [20, 20, 100, 80], [50, 50, 70, 70], [10, 10, 20, 20]],
    )
    resultado = SimpleNamespace(boxes=boxes, masks=None)
    deteccoes = _filtrar_resultado_yolo(resultado, tamanho_frame_hw=(120, 120))

    # 2 cows: conf 0.85 passa e conf 0.3 passa (default: 0.25)
    assert len(deteccoes) == 2
    assert all(isinstance(d, DeteccaoCow) for d in deteccoes)
    assert deteccoes[0].bbox == (20, 20, 100, 80)
    assert deteccoes[0].confianca == pytest.approx(0.85)


def test_descarta_abaixo_de_confianca_minima() -> None:
    class _Wrap:
        def __len__(self):
            return 2

    wrap = _Wrap()
    wrap.cls = np.array([COCO_COW_CLASS_ID, COCO_COW_CLASS_ID])
    wrap.conf = np.array([0.9, 0.1])
    wrap.xyxy = np.array([[0, 0, 10, 10], [20, 20, 30, 30]])
    resultado = SimpleNamespace(boxes=wrap, masks=None)

    deteccoes = _filtrar_resultado_yolo(
        resultado, tamanho_frame_hw=(50, 50), confianca_minima=0.5,
    )
    assert len(deteccoes) == 1
    assert deteccoes[0].confianca == pytest.approx(0.9)


def test_resultado_vazio() -> None:
    class _Wrap:
        def __len__(self):
            return 0

    wrap = _Wrap()
    wrap.cls = np.array([])
    wrap.conf = np.array([])
    wrap.xyxy = np.empty((0, 4))
    resultado = SimpleNamespace(boxes=wrap, masks=None)
    assert _filtrar_resultado_yolo(resultado, tamanho_frame_hw=(100, 100)) == []


def test_mascara_e_redimensionada_para_o_frame() -> None:
    class _Wrap:
        def __len__(self):
            return 1

    wrap = _Wrap()
    wrap.cls = np.array([COCO_COW_CLASS_ID])
    wrap.conf = np.array([0.9])
    wrap.xyxy = np.array([[10, 20, 90, 80]])

    # mascara 50x50 que precisa ser redimensionada para 120x160
    mascara_pequena = np.zeros((1, 50, 50), dtype=np.float32)
    mascara_pequena[0, 10:40, 10:40] = 1.0
    masks = SimpleNamespace(data=mascara_pequena)
    resultado = SimpleNamespace(boxes=wrap, masks=masks)

    deteccoes = _filtrar_resultado_yolo(resultado, tamanho_frame_hw=(120, 160))
    assert len(deteccoes) == 1
    assert deteccoes[0].mascara.shape == (120, 160)
    assert deteccoes[0].mascara.dtype == bool
    assert deteccoes[0].area_mascara_px > 0


def test_fallback_para_bbox_quando_sem_mascara() -> None:
    class _Wrap:
        def __len__(self):
            return 1

    wrap = _Wrap()
    wrap.cls = np.array([COCO_COW_CLASS_ID])
    wrap.conf = np.array([0.9])
    wrap.xyxy = np.array([[10, 20, 50, 60]])
    resultado = SimpleNamespace(boxes=wrap, masks=None)

    deteccoes = _filtrar_resultado_yolo(resultado, tamanho_frame_hw=(100, 100))
    assert len(deteccoes) == 1
    # Area = (50-10) * (60-20) = 40*40 = 1600
    assert deteccoes[0].area_mascara_px == 1600


@pytest.mark.ml
def test_detectar_cows_com_yolo_real() -> None:
    """Integracao com YOLO real. Baixa o peso na primeira execucao (~6 MB).

    Pulado se `ultralytics` nao estiver instalado (extra [ml] opcional).
    """
    ultralytics = pytest.importorskip("ultralytics")
    import cv2  # noqa: F401

    from indexbeef_vision.segmentation import carregar_modelo, detectar_cows

    modelo = carregar_modelo()
    # Frame branco 320x320 — nao deve detectar cow (teste do caminho feliz: nao crashar).
    frame = np.full((320, 320, 3), 255, dtype=np.uint8)
    deteccoes = detectar_cows(frame, modelo=modelo)
    assert isinstance(deteccoes, list)
