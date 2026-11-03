#!/usr/bin/env python3
"""Verifica novos modelos na API e baixa se disponíveis.

Uso:
    python atualizar_modelos.py --api-url http://localhost:8000 --modelos-dir /opt/indexbeef/modelos

Para cada modelo listado em MODELOS, consulta GET /modelos-versao/verificar-atualizacao.
Se houver versao nova, baixa o artefato e atualiza o arquivo .version local.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Erro: pacote 'requests' nao instalado. Execute: pip install requests", file=sys.stderr)
    sys.exit(1)

MODELOS = ["segmentacao", "keypoints_lateral", "peso"]


def verificar_e_baixar(api_url: str, modelos_dir: Path, nome: str) -> None:
    versao_file = modelos_dir / f"{nome}.version"
    versao_atual = versao_file.read_text().strip() if versao_file.exists() else "0.0.0"

    resp = requests.get(
        f"{api_url}/modelos-versao/verificar-atualizacao",
        params={"nome": nome, "versao_atual": versao_atual},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    if not data.get("atualizar"):
        print(f"[{nome}] versao {versao_atual} ja e a mais recente")
        return

    nova_versao = data["versao"]
    artefato_url = data.get("artefato_url")
    metricas = data.get("metricas", {})

    print(f"[{nome}] nova versao {nova_versao} disponivel (metricas: {metricas})")

    if not artefato_url:
        print(f"[{nome}] aviso: artefato_url nao disponivel, pulando download")
        versao_file.write_text(nova_versao)
        return

    print(f"[{nome}] baixando de {artefato_url} ...")
    r = requests.get(artefato_url, stream=True, timeout=120)
    r.raise_for_status()

    dest = modelos_dir / f"{nome}.onnx"
    dest.write_bytes(r.content)
    versao_file.write_text(nova_versao)

    tamanho_kb = dest.stat().st_size // 1024
    print(f"[{nome}] atualizado para {nova_versao} ({tamanho_kb} KB) -> {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Atualiza modelos ONNX do IndexBeef")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="URL base da IndexBeef API (padrao: http://localhost:8000)",
    )
    parser.add_argument(
        "--modelos-dir",
        default="./modelos",
        help="Diretorio local para salvar os modelos (padrao: ./modelos)",
    )
    parser.add_argument(
        "--modelos",
        nargs="*",
        default=MODELOS,
        help=f"Lista de modelos a verificar (padrao: {' '.join(MODELOS)})",
    )
    args = parser.parse_args()

    modelos_dir = Path(args.modelos_dir)
    modelos_dir.mkdir(parents=True, exist_ok=True)

    erros: list[str] = []
    for nome in args.modelos:
        try:
            verificar_e_baixar(args.api_url, modelos_dir, nome)
        except Exception as exc:
            print(f"[{nome}] erro: {exc}", file=sys.stderr)
            erros.append(nome)

    if erros:
        print(f"\nErros nos modelos: {', '.join(erros)}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nTodos os modelos verificados com sucesso.")


if __name__ == "__main__":
    main()
