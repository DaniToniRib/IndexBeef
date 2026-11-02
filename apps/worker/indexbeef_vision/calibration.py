"""Calibracao px <-> cm via marcadores ArUco (ver docs/04-pipeline-visao.md, secao 7).

A placa fisica tem lado conhecido (default 40 cm). Detectamos o marcador,
construimos a homografia que leva pontos da imagem para o plano da placa
em centimetros, e expomos:

- `px_por_cm`: escala media (lado medio em px / tamanho da placa em cm).
- `erro_reproj_px`: erro de reconstrucao dos cantos ao aplicar a homografia
  inversa. Com 4 cantos exatos (sem outliers), `getPerspectiveTransform` da
  um erro proximo de zero; o campo existe para quando houver mais pontos.
- `pixel_para_cm(ponto)`: aplica a homografia a um ponto da imagem.

Com duas placas (uma frontal, outra traseira) o docs/04 recomenda interpolar
a escala ao longo do animal; `Calibracao.px_por_cm` por enquanto e a media.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

DICIONARIO_PADRAO: int = cv2.aruco.DICT_4X4_50


class NenhumaPlacaDetectada(RuntimeError):
    """Nenhum marcador ArUco foi encontrado na imagem."""


@dataclass(frozen=True)
class CalibracaoPlaca:
    aruco_id: int
    cantos_px: np.ndarray  # (4, 2) float32 na ordem TL, TR, BR, BL
    homografia: np.ndarray  # (3, 3) float, mapeia pixel -> cm
    px_por_cm: float
    erro_reproj_px: float


@dataclass(frozen=True)
class Calibracao:
    placas: tuple[CalibracaoPlaca, ...]
    tamanho_placa_cm: float
    dicionario_id: int

    @property
    def px_por_cm(self) -> float:
        return float(np.mean([p.px_por_cm for p in self.placas]))

    def pixel_para_cm(
        self, ponto_px: tuple[float, float], placa_idx: int = 0,
    ) -> tuple[float, float]:
        placa = self.placas[placa_idx]
        pts = np.array([[[ponto_px[0], ponto_px[1]]]], dtype=np.float32)
        transformado = cv2.perspectiveTransform(pts, placa.homografia)
        return float(transformado[0, 0, 0]), float(transformado[0, 0, 1])


def _cantos_cm(tamanho_placa_cm: float) -> np.ndarray:
    return np.array(
        [
            [0.0, 0.0],
            [tamanho_placa_cm, 0.0],
            [tamanho_placa_cm, tamanho_placa_cm],
            [0.0, tamanho_placa_cm],
        ],
        dtype=np.float32,
    )


def _lado_medio_px(cantos_px: np.ndarray) -> float:
    lados = [
        float(np.linalg.norm(cantos_px[0] - cantos_px[1])),
        float(np.linalg.norm(cantos_px[1] - cantos_px[2])),
        float(np.linalg.norm(cantos_px[2] - cantos_px[3])),
        float(np.linalg.norm(cantos_px[3] - cantos_px[0])),
    ]
    return float(np.mean(lados))


def detectar_placas(
    imagem: np.ndarray,
    dicionario_id: int = DICIONARIO_PADRAO,
) -> list[tuple[int, np.ndarray]]:
    """Detecta marcadores ArUco. Retorna lista de (aruco_id, cantos 4x2 float32)."""
    dicio = cv2.aruco.getPredefinedDictionary(dicionario_id)
    detector = cv2.aruco.ArucoDetector(dicio)
    cantos, ids, _ = detector.detectMarkers(imagem)
    if ids is None:
        return []
    deteccoes: list[tuple[int, np.ndarray]] = []
    for i, aruco_id in enumerate(ids.flatten()):
        pts = cantos[i].reshape(4, 2).astype(np.float32)
        deteccoes.append((int(aruco_id), pts))
    return deteccoes


def calcular_homografia_placa(
    cantos_px: np.ndarray,
    tamanho_placa_cm: float,
) -> tuple[np.ndarray, float]:
    """Retorna (homografia pixel->cm, erro de reprojeção médio em px)."""
    cantos_px_f = cantos_px.astype(np.float32)
    cantos_cm = _cantos_cm(tamanho_placa_cm)
    H = cv2.getPerspectiveTransform(cantos_px_f, cantos_cm)
    H_inv = np.linalg.inv(H)
    reconstruido = cv2.perspectiveTransform(
        cantos_cm.reshape(-1, 1, 2), H_inv,
    ).reshape(-1, 2)
    erros = np.linalg.norm(reconstruido - cantos_px_f, axis=1)
    return H, float(np.mean(erros))


def calibrar(
    imagem: np.ndarray,
    tamanho_placa_cm: float = 40.0,
    dicionario_id: int = DICIONARIO_PADRAO,
) -> Calibracao:
    """Executa o pipeline de calibracao numa imagem.

    Levanta `NenhumaPlacaDetectada` quando nenhum marcador e encontrado.
    """
    deteccoes = detectar_placas(imagem, dicionario_id)
    if not deteccoes:
        raise NenhumaPlacaDetectada(
            "Nenhum marcador ArUco detectado. Verifique iluminacao, nitidez "
            "e se a placa esta inteira no quadro.",
        )
    placas: list[CalibracaoPlaca] = []
    for aruco_id, cantos_px in deteccoes:
        H, erro = calcular_homografia_placa(cantos_px, tamanho_placa_cm)
        px_por_cm = _lado_medio_px(cantos_px) / tamanho_placa_cm
        placas.append(
            CalibracaoPlaca(
                aruco_id=aruco_id,
                cantos_px=cantos_px,
                homografia=H,
                px_por_cm=px_por_cm,
                erro_reproj_px=erro,
            ),
        )
    return Calibracao(
        placas=tuple(placas),
        tamanho_placa_cm=tamanho_placa_cm,
        dicionario_id=dicionario_id,
    )
