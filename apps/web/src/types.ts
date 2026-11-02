// Tipos do dominio frontend. Keypoints laterais vem do docs/04-pipeline-visao.md, secao 6.

export type KeypointId =
  | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8
  | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17;

export interface Keypoint {
  id: KeypointId;
  x: number; // pixel na imagem (nao normalizado)
  y: number;
  corrigido?: boolean; // marca quando o usuario arrastou o ponto
  confianca?: number; // 0..1 vindo do modelo (ausente na Fase 0)
}

export const NOMES_KEYPOINTS: Readonly<Record<KeypointId, string>> = {
  0: "Focinho",
  1: "Nuca",
  2: "Topo do cupim",
  3: "Cernelha",
  4: "Meio do dorso",
  5: "Lombo",
  6: "Ilio",
  7: "Isquio",
  8: "Insercao da cauda",
  9: "Ponta da espadua",
  10: "Cilha superior",
  11: "Cilha inferior",
  12: "Umbigo / bainha",
  13: "Ponto mais baixo do ventre",
  14: "Joelho (anterior)",
  15: "Casco anterior",
  16: "Jarrete",
  17: "Casco posterior",
} as const;

export const IDS_KEYPOINTS: readonly KeypointId[] = [
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
] as const;
