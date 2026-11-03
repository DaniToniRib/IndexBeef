"""Testes do modulo de inferencia de keypoints YOLO-pose."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from indexbeef_vision.keypoints_inference import (
    NUM_KEYPOINTS,
    KeypointPredito,
    carregar_modelo_keypoints,
    predizer_keypoints,
)


def _frame_sintetico() -> np.ndarray:
    return np.zeros((720, 1280, 3), dtype=np.uint8)


def _mock_modelo_com_keypoints(n_kpts: int, conf_valor: float = 0.9) -> MagicMock:
    """Cria um mock de modelo YOLO-pose que retorna n_kpts keypoints."""
    modelo = MagicMock()

    xy = np.zeros((n_kpts, 2), dtype=np.float32)
    for i in range(n_kpts):
        xy[i] = [float(10 + i * 5), float(20 + i * 3)]

    conf = np.full((n_kpts,), conf_valor, dtype=np.float32)

    kpts_mock = MagicMock()
    kpts_mock.xy = [MagicMock()]
    kpts_mock.xy[0].cpu.return_value.numpy.return_value = xy
    kpts_mock.conf = [MagicMock()]
    kpts_mock.conf[0].cpu.return_value.numpy.return_value = conf

    resultado_mock = MagicMock()
    resultado_mock.keypoints = kpts_mock

    modelo.predict.return_value = [resultado_mock]
    return modelo


# ---------------------------------------------------------------------------
# 1. carregar_modelo_keypoints sem env var → None
# ---------------------------------------------------------------------------


def test_carregar_modelo_sem_env_var_retorna_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INDEXBEEF_KEYPOINTS_MODEL", "")
    resultado = carregar_modelo_keypoints(None)
    assert resultado is None


# ---------------------------------------------------------------------------
# 2. carregar_modelo_keypoints com caminho inexistente → None
# ---------------------------------------------------------------------------


def test_carregar_modelo_caminho_inexistente_retorna_none() -> None:
    resultado = carregar_modelo_keypoints("/nao/existe/modelo.pt")
    assert resultado is None


# ---------------------------------------------------------------------------
# 3. predizer_keypoints com modelo None → None
# ---------------------------------------------------------------------------


def test_predizer_keypoints_modelo_none_retorna_none() -> None:
    frame = _frame_sintetico()
    resultado = predizer_keypoints(frame, None)
    assert resultado is None


# ---------------------------------------------------------------------------
# 4. predizer_keypoints com mock de 18 keypoints → lista de 18
# ---------------------------------------------------------------------------


def test_predizer_keypoints_18_kpts_retorna_lista() -> None:
    frame = _frame_sintetico()
    modelo = _mock_modelo_com_keypoints(NUM_KEYPOINTS, conf_valor=0.9)

    resultado = predizer_keypoints(frame, modelo, confianca_minima=0.3)

    assert resultado is not None
    assert len(resultado) == NUM_KEYPOINTS
    for i, kp in enumerate(resultado):
        assert isinstance(kp, KeypointPredito)
        assert kp.id == i
        assert kp.confianca == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# 5. predizer_keypoints com numero errado de keypoints → None
# ---------------------------------------------------------------------------


def test_predizer_keypoints_numero_errado_retorna_none() -> None:
    frame = _frame_sintetico()
    modelo = _mock_modelo_com_keypoints(17)  # deveria ser 18

    resultado = predizer_keypoints(frame, modelo)
    assert resultado is None


# ---------------------------------------------------------------------------
# 6. predizer_keypoints filtra por confianca_minima
# ---------------------------------------------------------------------------


def test_predizer_keypoints_filtra_baixa_confianca() -> None:
    frame = _frame_sintetico()

    # Primeiro kpt tem confianca 0.1, resto 0.9
    modelo = _mock_modelo_com_keypoints(NUM_KEYPOINTS, conf_valor=0.9)
    conf_array = np.full((NUM_KEYPOINTS,), 0.9, dtype=np.float32)
    conf_array[0] = 0.1  # abaixo do limiar
    modelo.predict.return_value[0].keypoints.conf[0].cpu.return_value.numpy.return_value = conf_array

    resultado = predizer_keypoints(frame, modelo, confianca_minima=0.5)

    assert resultado is not None
    ids = [kp.id for kp in resultado]
    assert 0 not in ids  # kp 0 filtrado por baixa confianca
    assert len(resultado) == NUM_KEYPOINTS - 1
