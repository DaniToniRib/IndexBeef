"""Gera o PDF da placa ArUco de calibracao do IndexBeef.

Ver docs/03-captura.md, secao "Calibracao".

A placa final e impressa em plotter sobre PVC/ACM, no tamanho fisico correto
(40 cm por padrao). O PDF e gerado NO TAMANHO REAL para que a graefica
reproduza as dimensoes sem reescalonamento (opcao `--formato tamanho-real`,
que e o default).

A opcao `--formato a3` gera o marcador reduzido centralizado numa folha A3
paisagem para prototipagem em bancada. Nao usar em campo: a escala sera
diferente da declarada.

Dicionario fixo: DICT_4X4_50. Dois IDs no MVP:
- ID 0: placa frontal (lado do flanco)
- ID 1: placa traseira (atras do corredor)

Uso:

    python hardware/gerar_placa_aruco.py                     # id=0, 40x40 cm
    python hardware/gerar_placa_aruco.py --id 1 \
        --saida hardware/placa-aruco-40cm-id1.pdf
    python hardware/gerar_placa_aruco.py --formato a3 \
        --saida hardware/placa-aruco-a3-proto.pdf

Dependencias: ver hardware/requirements.txt (opencv-contrib-python-headless,
reportlab, pillow, numpy).
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

DICIONARIO = cv2.aruco.DICT_4X4_50
DICIONARIO_NOME = "DICT_4X4_50"


def gerar_imagem_marcador(aruco_id: int, pixels_lado: int = 2000) -> np.ndarray:
    """Gera a imagem do marcador ArUco como ndarray 2D (uint8, 0/255).

    `pixels_lado` controla a resolucao da imagem; para plotter, 2000 px da
    uma densidade confortavel em 40 cm (~127 dpi) e pode ser aumentada.
    """
    aruco_dict = cv2.aruco.getPredefinedDictionary(DICIONARIO)
    return cv2.aruco.generateImageMarker(aruco_dict, aruco_id, pixels_lado)


def _imagem_para_reader(img: np.ndarray) -> ImageReader:
    pil = Image.fromarray(img, mode="L")
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _desenhar_rotulo(c: canvas.Canvas, texto: str, x_cm: float, y_cm: float) -> None:
    c.setFont("Helvetica", 8)
    c.drawString(x_cm * cm, y_cm * cm, texto)


def gerar_pdf_tamanho_real(
    aruco_id: int,
    saida: Path,
    tamanho_cm: float = 40.0,
    margem_cm: float = 2.0,
    pixels_lado: int = 2000,
) -> Path:
    """Gera o PDF do tamanho fisico final da placa (default 40x40 cm + margem).

    A margem funciona como quiet zone: ArUco recomenda ao menos 1 modulo
    livre em volta; `margem_cm = 2.0` ja garante margem suficiente para
    DICT_4X4_50 a 40 cm.
    """
    lado_total_cm = tamanho_cm + 2 * margem_cm
    lado_total_pt = lado_total_cm * cm
    saida.parent.mkdir(parents=True, exist_ok=True)

    reader = _imagem_para_reader(gerar_imagem_marcador(aruco_id, pixels_lado))

    c = canvas.Canvas(str(saida), pagesize=(lado_total_pt, lado_total_pt))
    c.drawImage(
        reader,
        margem_cm * cm,
        margem_cm * cm,
        tamanho_cm * cm,
        tamanho_cm * cm,
        preserveAspectRatio=True,
    )
    rotulo = (
        f"IndexBeef | ArUco {DICIONARIO_NOME} id={aruco_id} | "
        f"{tamanho_cm:.0f}x{tamanho_cm:.0f} cm | imprimir no tamanho real"
    )
    _desenhar_rotulo(c, rotulo, margem_cm, margem_cm / 2)
    c.showPage()
    c.save()
    return saida


def gerar_pdf_a3(
    aruco_id: int,
    saida: Path,
    tamanho_cm_logico: float = 40.0,
    pixels_lado: int = 1500,
) -> Path:
    """Variante A3 (paisagem) para prototipagem em bancada.

    Imprime o marcador centralizado, reduzido para caber na folha. A escala
    nao e a de campo — a imagem gerada tem lado = (menor dimensao da folha) -
    2*margem, por isso o PDF resultante nao deve ser usado para calibrar
    medidas reais; so para testar o pipeline de deteccao.
    """
    page = landscape(A3)
    largura_pt, altura_pt = page
    margem_cm_fisica = 1.5
    lado_marcador_pt = min(largura_pt, altura_pt) - 2 * margem_cm_fisica * cm
    saida.parent.mkdir(parents=True, exist_ok=True)

    reader = _imagem_para_reader(gerar_imagem_marcador(aruco_id, pixels_lado))

    c = canvas.Canvas(str(saida), pagesize=page)
    x = (largura_pt - lado_marcador_pt) / 2
    y = (altura_pt - lado_marcador_pt) / 2
    c.drawImage(reader, x, y, lado_marcador_pt, lado_marcador_pt, preserveAspectRatio=True)
    rotulo = (
        f"IndexBeef | ArUco {DICIONARIO_NOME} id={aruco_id} | "
        f"PROTOTIPO A3 (nao usar em campo) | dimensao fisica alvo: "
        f"{tamanho_cm_logico:.0f}x{tamanho_cm_logico:.0f} cm"
    )
    _desenhar_rotulo(c, rotulo, margem_cm_fisica, margem_cm_fisica / 2)
    c.showPage()
    c.save()
    return saida


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera o PDF da placa ArUco do IndexBeef (DICT_4X4_50).",
    )
    parser.add_argument(
        "--id",
        type=int,
        default=0,
        dest="aruco_id",
        help="ID do marcador no dicionario DICT_4X4_50 (default: 0).",
    )
    parser.add_argument(
        "--tamanho-cm",
        type=float,
        default=40.0,
        help="Lado do marcador em cm (default: 40).",
    )
    parser.add_argument(
        "--margem-cm",
        type=float,
        default=2.0,
        help="Margem branca (quiet zone) em cm (default: 2).",
    )
    parser.add_argument(
        "--formato",
        choices=["tamanho-real", "a3"],
        default="tamanho-real",
        help="tamanho-real = PDF do tamanho fisico (default). a3 = prototipagem.",
    )
    parser.add_argument(
        "--pixels-lado",
        type=int,
        default=2000,
        help="Resolucao da imagem do marcador em pixels por lado (default: 2000).",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=None,
        help="Caminho do PDF de saida (default depende do formato e do ID).",
    )
    args = parser.parse_args()

    if args.saida is None:
        if args.formato == "a3":
            args.saida = Path(f"hardware/placa-aruco-a3-proto-id{args.aruco_id}.pdf")
        else:
            args.saida = Path(
                f"hardware/placa-aruco-{args.tamanho_cm:.0f}cm-id{args.aruco_id}.pdf",
            )

    if args.formato == "a3":
        gerar_pdf_a3(args.aruco_id, args.saida, args.tamanho_cm, args.pixels_lado)
    else:
        gerar_pdf_tamanho_real(
            args.aruco_id,
            args.saida,
            args.tamanho_cm,
            args.margem_cm,
            args.pixels_lado,
        )
    print(f"PDF gerado: {args.saida.resolve()}")


if __name__ == "__main__":
    main()
