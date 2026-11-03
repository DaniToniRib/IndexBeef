#!/usr/bin/env python3
"""Exporta modelo YOLO-pose para ONNX.

Uso:
    python exportar_onnx.py --modelo best.pt --saida model.onnx --tamanho 640

O arquivo ONNX sera salvo no mesmo diretorio do .pt pelo ultralytics; se --saida
for diferente do padrao, o script tenta mover o arquivo para o destino indicado.

Requisitos:
    pip install ultralytics onnx onnxsim
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta modelo YOLO-pose para ONNX")
    parser.add_argument("--modelo", required=True, help="Caminho para o arquivo .pt treinado")
    parser.add_argument("--saida", required=True, help="Caminho de saida para o .onnx")
    parser.add_argument(
        "--tamanho",
        type=int,
        default=640,
        help="Tamanho de entrada do modelo (padrao: 640)",
    )
    args = parser.parse_args()

    modelo_path = Path(args.modelo)
    if not modelo_path.exists():
        print(f"Erro: arquivo de modelo nao encontrado: {modelo_path}", file=sys.stderr)
        sys.exit(1)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("Erro: pacote 'ultralytics' nao instalado. Execute: pip install ultralytics", file=sys.stderr)
        sys.exit(1)

    print(f"Carregando modelo: {modelo_path}")
    model = YOLO(str(modelo_path))

    print(f"Exportando para ONNX (imgsz={args.tamanho}, simplify=True)...")
    model.export(format="onnx", imgsz=args.tamanho, simplify=True)

    # ultralytics salva no mesmo diretorio do .pt com extensao .onnx
    saida_padrao = modelo_path.with_suffix(".onnx")
    saida_destino = Path(args.saida)

    if saida_padrao.exists() and saida_padrao != saida_destino:
        saida_destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(saida_padrao), str(saida_destino))
        print(f"Arquivo movido para: {saida_destino}")

    if saida_destino.exists():
        tamanho_kb = saida_destino.stat().st_size // 1024
        print(f"Exportado com sucesso: {saida_destino} ({tamanho_kb} KB)")
    else:
        # ultralytics pode salvar em subdiretorio runs/
        print(
            f"Exportacao concluida. Verifique o diretorio do modelo ou runs/ para o arquivo .onnx.",
        )


if __name__ == "__main__":
    main()
