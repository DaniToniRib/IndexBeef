// Utilitarios puros para manipulacao dos 18 keypoints laterais.
// Mantidos sem dependencia do React para facilitar o teste e a reutilizacao.

import { IDS_KEYPOINTS, type Keypoint, type KeypointId } from "./types";

export function clampNoCanvas(valor: number, max: number): number {
  if (!Number.isFinite(valor)) return 0;
  if (valor < 0) return 0;
  if (valor > max) return max;
  return valor;
}

export function aplicarDelta(
  pontos: readonly Keypoint[],
  id: KeypointId,
  dx: number,
  dy: number,
  largura: number,
  altura: number,
): Keypoint[] {
  return pontos.map((p) =>
    p.id === id
      ? {
          ...p,
          x: clampNoCanvas(p.x + dx, largura),
          y: clampNoCanvas(p.y + dy, altura),
          corrigido: true,
        }
      : p,
  );
}

export function moverPara(
  pontos: readonly Keypoint[],
  id: KeypointId,
  x: number,
  y: number,
  largura: number,
  altura: number,
): Keypoint[] {
  return pontos.map((p) =>
    p.id === id
      ? {
          ...p,
          x: clampNoCanvas(x, largura),
          y: clampNoCanvas(y, altura),
          corrigido: true,
        }
      : p,
  );
}

/**
 * Posicoes iniciais aproximadas em um frame NORMALIZADO (0..1 em x e y),
 * dispostas no formato lateral de um bovino de pe, de perfil, cabeca a esquerda.
 * O chamador multiplica por largura/altura para converter em pixels.
 */
const POSICOES_PADRAO_NORMALIZADAS: Readonly<Record<KeypointId, [number, number]>> = {
  0: [0.08, 0.42], // focinho
  1: [0.17, 0.33], // nuca
  2: [0.28, 0.28], // topo do cupim
  3: [0.32, 0.35], // cernelha
  4: [0.5, 0.37], // meio do dorso
  5: [0.65, 0.4], // lombo
  6: [0.75, 0.42], // ilio
  7: [0.88, 0.46], // isquio
  8: [0.9, 0.4], // insercao da cauda
  9: [0.3, 0.45], // ponta da espadua
  10: [0.4, 0.5], // cilha superior (dorso atras da paleta)
  11: [0.4, 0.78], // cilha inferior (esterno)
  12: [0.6, 0.82], // umbigo / bainha
  13: [0.55, 0.85], // ponto mais baixo do ventre
  14: [0.32, 0.82], // joelho anterior
  15: [0.32, 0.95], // casco anterior
  16: [0.78, 0.82], // jarrete
  17: [0.82, 0.95], // casco posterior
};

export function pontosIniciaisPadrao(largura: number, altura: number): Keypoint[] {
  return IDS_KEYPOINTS.map((id) => {
    const [nx, ny] = POSICOES_PADRAO_NORMALIZADAS[id];
    return { id, x: nx * largura, y: ny * altura, corrigido: false };
  });
}
