"""Testes da task preparar_frames_avaliacao."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest


def _frame_jpeg(tmp_path: Path) -> Path:
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (10, 10), (90, 90), (200, 200, 200), 2)
    p = tmp_path / "frame.jpg"
    cv2.imwrite(str(p), img)
    return p


def _mock_engine(row):
    """Cria mock de engine SQLAlchemy com fetchone fixo."""
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = row

    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    engine.connect.return_value.__exit__.return_value = False
    engine.begin.return_value.__enter__.return_value = conn
    engine.begin.return_value.__exit__.return_value = False

    return engine, conn


def test_preparar_frames_avaliacao_sucesso(tmp_path: Path) -> None:
    """Fluxo feliz: baixa vídeo, seleciona melhor frame, sobe ao MinIO e registra captura."""
    from indexbeef_vision.frames import FrameExtraido
    from indexbeef_worker.tasks import preparar_frames_avaliacao

    frame_path = _frame_jpeg(tmp_path)
    melhor = FrameExtraido(indice=1, arquivo=frame_path, tempo_s=0.2)
    engine, conn = _mock_engine(("http://minio/video.mp4", "av-uuid-001", "lateral"))

    with (
        patch("indexbeef_worker.tasks._db_engine", return_value=engine),
        patch("indexbeef_worker.tasks.minio_download", return_value=b"fake-video"),
        patch("indexbeef_worker.tasks.extrair_frames", return_value=[melhor]),
        patch("indexbeef_worker.tasks.selecionar_melhor_frame", return_value=melhor),
        patch("indexbeef_worker.tasks.minio_upload", return_value="http://minio/frame.jpg") as mock_up,
    ):
        preparar_frames_avaliacao("cap-id-xyz")

    mock_up.assert_called_once()
    upload_args = mock_up.call_args[0]
    assert upload_args[1] == "image/jpeg"
    assert upload_args[2] == "jpg"

    last_exec = conn.execute.call_args_list[-1]
    sql_str = str(last_exec[0][0])
    assert "INSERT INTO captura" in sql_str
    params = last_exec[0][1]
    assert params["url"] == "http://minio/frame.jpg"
    assert params["avaliacao_id"] == "av-uuid-001"
    assert params["vista"] == "lateral"


def test_preparar_frames_avaliacao_sem_frames_nao_insere() -> None:
    """Quando nenhum frame é extraído, a task retorna sem inserir no banco."""
    from indexbeef_worker.tasks import preparar_frames_avaliacao

    engine, _ = _mock_engine(("http://minio/video.mp4", "av-uuid-002", "lateral"))

    with (
        patch("indexbeef_worker.tasks._db_engine", return_value=engine),
        patch("indexbeef_worker.tasks.minio_download", return_value=b"fake"),
        patch("indexbeef_worker.tasks.extrair_frames", return_value=[]),
        patch("indexbeef_worker.tasks.selecionar_melhor_frame", return_value=None),
    ):
        preparar_frames_avaliacao("cap-id-sem-frames")

    engine.begin.assert_not_called()


def test_preparar_frames_avaliacao_captura_nao_encontrada() -> None:
    """Quando o registro não existe no banco, deve lançar ValueError."""
    from indexbeef_worker.tasks import preparar_frames_avaliacao

    engine, _ = _mock_engine(None)

    with (
        patch("indexbeef_worker.tasks._db_engine", return_value=engine),
        pytest.raises(ValueError, match="nao encontrada"),
    ):
        preparar_frames_avaliacao("cap-id-inexistente")
