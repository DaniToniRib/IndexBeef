from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SyncMixin


class ModeloVersao(SyncMixin, Base):
    """Registro de versoes de modelos ML treinados (ver docs/08-roadmap.md Fase 3).

    nome: "segmentacao" | "keypoints_lateral" | "peso" | "ecc" | ...
    versao: semver, e.g. "0.1.0"
    metricas: JSON com metricas de avaliacao, e.g. {"mAP": 0.82, "MAPE": 0.048}
    artefato_url: URL MinIO/S3 para o arquivo .pt ou .json do modelo
    ativo: True = este e o modelo corrente para o nome dado
    descricao: texto livre com notas sobre o treinamento
    """

    __tablename__ = "modelo_versao"

    nome: Mapped[str] = mapped_column(String, nullable=False, index=True)
    versao: Mapped[str] = mapped_column(String, nullable=False)
    metricas: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    artefato_url: Mapped[str | None] = mapped_column(String, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
