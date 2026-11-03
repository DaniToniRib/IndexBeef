"""Inferencia ONNX de keypoints — alternativa ao PyTorch para dispositivos sem GPU.

Usado quando o modelo YOLO-pose tiver sido exportado para ONNX (ml/train/exportar_onnx.py).
Retorna a mesma estrutura que predizer_keypoints() em keypoints_inference.py.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

try:
    import onnxruntime as ort

    _ORT_OK = True
except ImportError:
    _ORT_OK = False

NUM_KEYPOINTS = 18


def carregar_sessao_onnx(caminho: str | Path) -> "ort.InferenceSession | None":
    """Carrega uma InferenceSession ONNX a partir do caminho dado.

    Retorna None se onnxruntime nao estiver instalado ou o arquivo nao existir.
    """
    if not _ORT_OK or not Path(str(caminho)).exists():
        return None
    try:
        return ort.InferenceSession(str(caminho), providers=["CPUExecutionProvider"])
    except Exception:
        return None


def predizer_keypoints_onnx(
    frame: np.ndarray,
    sessao: "ort.InferenceSession | None",
    confianca_minima: float = 0.3,
) -> list | None:
    """Executa inferencia ONNX de keypoints em um frame BGR/RGB.

    Retorna lista de dicts com {ponto_id, x, y, confianca} (coordenadas normalizadas 0-1)
    ou None se nao houver deteccao acima de confianca_minima.

    Formato de saida esperado do modelo YOLO-pose exportado:
      shape (1, 57, N): 57 = 5 (xywh+conf) + 18*3 (kp_x, kp_y, kp_conf)
    """
    if sessao is None:
        return None
    try:
        h, w = frame.shape[:2]
        # Pre-processamento: float32 normalizado, NCHW
        img = frame.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))[np.newaxis]  # (1, C, H, W)

        nome_entrada = sessao.get_inputs()[0].name
        saida = sessao.run(None, {nome_entrada: img})[0]  # (1, 57, N)

        if saida.ndim != 3 or saida.shape[0] != 1:
            return None

        # Selecionar deteccao com maior confianca (indice 4)
        confs = saida[0, 4, :]
        if confs.size == 0:
            return None
        idx = int(np.argmax(confs))
        if confs[idx] < confianca_minima:
            return None

        # Extrair keypoints: indices 5+ (18 kp * 3 valores)
        kps_flat = saida[0, 5:, idx]
        if len(kps_flat) < NUM_KEYPOINTS * 3:
            return None

        resultado = []
        for i in range(NUM_KEYPOINTS):
            x = float(kps_flat[i * 3])
            y = float(kps_flat[i * 3 + 1])
            c = float(kps_flat[i * 3 + 2])
            resultado.append({
                "ponto_id": i,
                "x": x / w,
                "y": y / h,
                "confianca": c,
            })
        return resultado
    except Exception:
        return None
