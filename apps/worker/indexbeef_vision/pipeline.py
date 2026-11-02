"""Orquestração do pipeline. Implementação completa virá na Fase 1."""

from __future__ import annotations

VERSAO_PIPELINE = "0.1.0"


def ping() -> dict[str, str]:
    return {"status": "ok", "pipeline": VERSAO_PIPELINE}
