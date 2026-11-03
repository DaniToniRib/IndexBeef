#!/usr/bin/env python
"""Exporta keypoints em formato COCO via a API.

Uso:
    python ml/train/exportar_coco_cli.py \\
        --api http://localhost:8000 \\
        --fazenda-id UUID \\
        --saida ml/datasets/keypoints_coco.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import requests
    _REQUESTS_DISPONIVEL = True
except ImportError:
    _REQUESTS_DISPONIVEL = False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exporta anotacoes de keypoints da API no formato COCO",
    )
    parser.add_argument(
        "--api",
        default="http://localhost:8000",
        help="URL base da API IndexBeef (padrao: http://localhost:8000)",
    )
    parser.add_argument(
        "--fazenda-id",
        default=None,
        help="UUID da fazenda para filtrar (opcional)",
    )
    parser.add_argument(
        "--animal-id",
        default=None,
        help="UUID do animal para filtrar (opcional)",
    )
    parser.add_argument(
        "--saida",
        default="ml/datasets/keypoints_coco.json",
        help="Arquivo de saida (.json)",
    )
    args = parser.parse_args()

    if not _REQUESTS_DISPONIVEL:
        print("Erro: biblioteca 'requests' nao encontrada. Instale: pip install requests")
        sys.exit(1)

    # Montar URL com filtros opcionais
    url = f"{args.api.rstrip('/')}/avaliacoes/exportar-coco"
    params: dict[str, str] = {}
    if args.fazenda_id:
        params["fazenda_id"] = args.fazenda_id
    if args.animal_id:
        params["animal_id"] = args.animal_id

    print(f"Exportando de: {url}")
    if params:
        print(f"  Filtros: {params}")

    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Erro ao chamar a API: {e}")
        sys.exit(1)

    data = resp.json()
    n_imagens = len(data.get("images", []))
    n_anotacoes = len(data.get("annotations", []))
    print(f"  {n_imagens} imagens, {n_anotacoes} anotacoes")

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"COCO exportado para: {saida}")
    print("\nProximos passos:")
    print("  1. Importe o arquivo no CVAT (Create task → Upload annotation → COCO 1.0)")
    print("  2. Revise/corrija os keypoints")
    print("  3. Exporte no formato COCO Keypoints para treinar o YOLO-pose")
    print("  4. yolo pose train data=indexbeef_pose.yaml model=yolov8n-pose.pt epochs=100")


if __name__ == "__main__":
    main()
