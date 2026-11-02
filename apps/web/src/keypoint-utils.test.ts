import { describe, expect, it } from "vitest";
import {
  aplicarDelta,
  clampNoCanvas,
  moverPara,
  pontosIniciaisPadrao,
} from "./keypoint-utils";
import { IDS_KEYPOINTS, NOMES_KEYPOINTS } from "./types";

describe("constantes do dominio", () => {
  it("tem 18 keypoints laterais", () => {
    expect(IDS_KEYPOINTS).toHaveLength(18);
    expect(Object.keys(NOMES_KEYPOINTS)).toHaveLength(18);
  });

  it("usa os nomes do docs/04 (focinho ... casco posterior)", () => {
    expect(NOMES_KEYPOINTS[0]).toBe("Focinho");
    expect(NOMES_KEYPOINTS[3]).toBe("Cernelha");
    expect(NOMES_KEYPOINTS[6]).toBe("Ilio");
    expect(NOMES_KEYPOINTS[17]).toBe("Casco posterior");
  });
});

describe("clampNoCanvas", () => {
  it("mantem no intervalo [0, max]", () => {
    expect(clampNoCanvas(50, 100)).toBe(50);
    expect(clampNoCanvas(-10, 100)).toBe(0);
    expect(clampNoCanvas(150, 100)).toBe(100);
  });

  it("trata NaN/Infinity como zero (robustez de SVG)", () => {
    expect(clampNoCanvas(Number.NaN, 100)).toBe(0);
    expect(clampNoCanvas(Number.POSITIVE_INFINITY, 100)).toBe(0);
  });
});

describe("pontosIniciaisPadrao", () => {
  it("gera 18 pontos dentro do canvas", () => {
    const pontos = pontosIniciaisPadrao(1280, 720);
    expect(pontos).toHaveLength(18);
    for (const p of pontos) {
      expect(p.x).toBeGreaterThanOrEqual(0);
      expect(p.x).toBeLessThanOrEqual(1280);
      expect(p.y).toBeGreaterThanOrEqual(0);
      expect(p.y).toBeLessThanOrEqual(720);
      expect(p.corrigido).toBe(false);
    }
  });
});

describe("moverPara e aplicarDelta", () => {
  it("moverPara atualiza apenas o ponto alvo e marca como corrigido", () => {
    const pontos = pontosIniciaisPadrao(1000, 1000);
    const atualizado = moverPara(pontos, 3, 500, 500, 1000, 1000);
    const alvo = atualizado.find((p) => p.id === 3)!;
    expect(alvo.x).toBe(500);
    expect(alvo.y).toBe(500);
    expect(alvo.corrigido).toBe(true);
    // outros nao mudaram
    for (const p of atualizado) {
      if (p.id !== 3) {
        expect(p.corrigido).toBe(false);
      }
    }
  });

  it("aplicarDelta soma e clampa nas bordas", () => {
    const pontos = pontosIniciaisPadrao(100, 100);
    const atualizado = aplicarDelta(pontos, 0, -9999, -9999, 100, 100);
    const alvo = atualizado.find((p) => p.id === 0)!;
    expect(alvo.x).toBe(0);
    expect(alvo.y).toBe(0);
    expect(alvo.corrigido).toBe(true);
  });
});
