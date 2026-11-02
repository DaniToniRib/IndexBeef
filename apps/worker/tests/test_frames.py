"""Testes do modulo frames (extracao de video)."""

from __future__ import annotations

from pathlib import Path

import pytest

from indexbeef_vision.frames import FrameExtraido, _calcular_passo, extrair_frames


def test_calcular_passo_arredonda_corretamente() -> None:
    # 30 fps -> 5 fps => passo = 6
    assert _calcular_passo(30, 5) == 6
    # 29.97 fps -> 5 fps => passo = round(5.994) = 6
    assert _calcular_passo(29.97, 5) == 6
    # fps_alvo >= fps_video => passo minimo 1
    assert _calcular_passo(10, 60) == 1


def test_calcular_passo_rejeita_valores_invalidos() -> None:
    with pytest.raises(ValueError):
        _calcular_passo(0, 5)
    with pytest.raises(ValueError):
        _calcular_passo(30, 0)


def test_extrair_frames_30fps_para_5fps(video_sintetico, tmp_path: Path) -> None:
    video = video_sintetico(fps=30, n_frames=60)  # 2 segundos
    destino = tmp_path / "frames"
    extraidos = extrair_frames(video, destino, fps_alvo=5.0)

    # 60 frames / passo 6 = 10 frames selecionados
    assert len(extraidos) == 10
    assert all(isinstance(f, FrameExtraido) for f in extraidos)
    assert all(f.arquivo.exists() and f.arquivo.suffix == ".jpg" for f in extraidos)
    # tempos crescentes
    tempos = [f.tempo_s for f in extraidos]
    assert tempos == sorted(tempos)
    # indices sao 0..N-1
    assert [f.indice for f in extraidos] == list(range(10))


def test_extrair_frames_rejeita_video_inexistente(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        extrair_frames(tmp_path / "nao_existe.mp4", tmp_path / "out", fps_alvo=5.0)


def test_extrair_frames_cria_destino(video_sintetico, tmp_path: Path) -> None:
    video = video_sintetico(fps=15, n_frames=15)
    destino = tmp_path / "nested" / "frames"
    assert not destino.exists()
    extraidos = extrair_frames(video, destino, fps_alvo=5.0)
    assert destino.is_dir()
    assert len(extraidos) == 5  # 15/3
