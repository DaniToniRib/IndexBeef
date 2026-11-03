"""Router de capturas (upload de fotos e videos para avaliacao).

POST /capturas/extrair-frame: recebe foto ou video, armazena no MinIO e,
  para videos, extrai o melhor frame (maior nitidez Laplaciana).
  Retorna { frame_url } pronto para o canvas de keypoints.

  Fallback: se MinIO indisponivel retorna 503.
  Para videos sem Redis disponivel, a extracao de frames e sincrona.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.minio_client import minio_disponivel, upload_bytes
from app.core.redis_queue import get_queue
from app.models.avaliacao import Avaliacao
from app.models.captura import Captura
from app.models.enums import TipoCaptura, VistaCaptura
from app.schemas.captura import CapturaCreate, CapturaRead, FrameExtraidoResponse

router = APIRouter(prefix="/capturas", tags=["capturas"])

_TIPOS_VIDEO = {
    "video/mp4", "video/quicktime", "video/x-msvideo",
    "video/x-matroska", "video/webm",
}
_TIPOS_IMAGEM = {"image/jpeg", "image/png", "image/webp", "image/bmp"}


def _extensao(nome: str, content_type: str) -> str:
    if "." in nome:
        return nome.rsplit(".", 1)[-1].lower()
    mapa = {
        "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp",
        "video/mp4": "mp4", "video/quicktime": "mov", "video/x-msvideo": "avi",
        "video/x-matroska": "mkv", "video/webm": "webm",
    }
    return mapa.get(content_type, "bin")


def _extrair_melhor_frame_sync(dados: bytes, extensao: str) -> bytes:
    """Extrai o melhor frame de um video em modo sincrono."""
    from indexbeef_vision.frames import extrair_frames
    from indexbeef_worker.frame_selector import selecionar_melhor_frame

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = Path(tmpdir) / f"video.{extensao}"
        video_path.write_bytes(dados)
        frames_dir = Path(tmpdir) / "frames"
        frames = extrair_frames(video_path, frames_dir, fps_alvo=5.0)
        melhor = selecionar_melhor_frame(frames)
        if melhor is None:
            raise RuntimeError("nenhum frame extraido do video")
        return melhor.arquivo.read_bytes()


@router.post(
    "/extrair-frame",
    response_model=FrameExtraidoResponse,
    status_code=status.HTTP_201_CREATED,
)
def extrair_frame(arquivo: UploadFile = File(...)) -> FrameExtraidoResponse:
    """Aceita foto ou video; retorna URL do frame pronto para anotacao."""
    if not minio_disponivel():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="armazenamento de arquivos indisponivel",
        )

    dados = arquivo.file.read()
    content_type = arquivo.content_type or "application/octet-stream"
    nome = arquivo.filename or "captura"
    ext = _extensao(nome, content_type)

    if content_type in _TIPOS_IMAGEM or ext in {"jpg", "jpeg", "png", "webp", "bmp"}:
        frame_bytes = dados
        frame_ext = ext
        frame_mime = content_type if content_type in _TIPOS_IMAGEM else "image/jpeg"
    elif content_type in _TIPOS_VIDEO or ext in {"mp4", "mov", "avi", "mkv", "webm"}:
        try:
            frame_bytes = _extrair_melhor_frame_sync(dados, ext)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"falha ao extrair frame do video: {e}",
            ) from e
        frame_ext = "jpg"
        frame_mime = "image/jpeg"
    else:
        raise HTTPException(
            status_code=415,
            detail=f"tipo de arquivo nao suportado: {content_type}",
        )

    frame_url = upload_bytes(frame_bytes, frame_mime, frame_ext)
    return FrameExtraidoResponse(frame_url=frame_url, tipo_mime=frame_mime)


@router.post("", response_model=CapturaRead, status_code=status.HTTP_201_CREATED)
def criar_captura(
    payload: CapturaCreate,
    db: Session = Depends(get_db),
) -> Captura:
    """Associa um arquivo (já no MinIO) a uma avaliação existente.

    Para tipo='video' com Redis disponível, enfileira preparar_frames_avaliacao
    para extração assíncrona do melhor frame.
    """
    avaliacao = db.get(Avaliacao, payload.avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status_code=404, detail="avaliacao nao encontrada")

    captura = Captura(
        avaliacao_id=payload.avaliacao_id,
        tipo=TipoCaptura(payload.tipo),
        vista=VistaCaptura(payload.vista),
        arquivo_url=payload.arquivo_url,
    )
    db.add(captura)
    db.flush()

    if payload.tipo == "video":
        fila = get_queue()
        if fila is not None:
            fila.enqueue(
                "indexbeef_worker.tasks.preparar_frames_avaliacao",
                str(captura.id),
                job_timeout=180,
            )

    db.commit()
    db.refresh(captura)
    return captura
