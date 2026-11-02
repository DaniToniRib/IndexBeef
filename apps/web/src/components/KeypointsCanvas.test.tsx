import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import { pontosIniciaisPadrao } from "../keypoint-utils";
import type { Keypoint } from "../types";
import { KeypointsCanvas } from "./KeypointsCanvas";

function Harness() {
  const [pontos, setPontos] = useState<Keypoint[]>(() => pontosIniciaisPadrao(1000, 1000));
  return <KeypointsCanvas pontos={pontos} largura={1000} altura={1000} onChange={setPontos} />;
}

describe("<KeypointsCanvas />", () => {
  it("renderiza os 18 keypoints", () => {
    render(<Harness />);
    for (let id = 0; id < 18; id++) {
      expect(screen.getByTestId(`kp-${id}`)).toBeInTheDocument();
    }
  });

  it("marca o ponto como corrigido apos pointerdown + pointermove + pointerup", () => {
    render(<Harness />);
    const alvo = screen.getByTestId("kp-6"); // ilio
    const svg = screen.getByRole("img");

    // mock de getBoundingClientRect para o svg (jsdom retorna 0s)
    const svgEl = svg as unknown as SVGSVGElement;
    svgEl.getBoundingClientRect = () =>
      ({
        left: 0,
        top: 0,
        right: 1000,
        bottom: 1000,
        width: 1000,
        height: 1000,
      }) as DOMRect;

    (alvo as unknown as SVGCircleElement).setPointerCapture = () => undefined;
    fireEvent.pointerDown(alvo, { clientX: 100, clientY: 100, pointerId: 1 });
    fireEvent.pointerMove(svg, { clientX: 500, clientY: 500, pointerId: 1 });
    fireEvent.pointerUp(svg, { clientX: 500, clientY: 500, pointerId: 1 });

    // fill verde = corrigido
    const atualizado = screen.getByTestId("kp-6");
    expect(atualizado.getAttribute("fill")).toBe("#22c55e");
  });
});
