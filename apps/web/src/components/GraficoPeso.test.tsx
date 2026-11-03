import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { PesagemHistorico } from "../api/client";
import { GraficoPeso } from "./GraficoPeso";

describe("<GraficoPeso />", () => {
  it("mostra fallback quando nao ha pesagens", () => {
    render(<GraficoPeso pesagens={[]} />);
    expect(screen.getByText(/sem pesagens/i)).toBeInTheDocument();
  });

  it("renderiza SVG com pontos para N pesagens", () => {
    const pesagens: PesagemHistorico[] = [
      {
        id: "1",
        data: "2026-01-01",
        peso_kg: "100",
        origem: "balanca",
        gmd_kg_dia: null,
      },
      {
        id: "2",
        data: "2026-02-01",
        peso_kg: "130",
        origem: "balanca",
        gmd_kg_dia: 0.97,
      },
      {
        id: "3",
        data: "2026-03-01",
        peso_kg: "160",
        origem: "balanca",
        gmd_kg_dia: 1.0,
      },
    ];
    const { container } = render(<GraficoPeso pesagens={pesagens} />);
    expect(screen.getByRole("img")).toBeInTheDocument();
    const circles = container.querySelectorAll("circle");
    expect(circles.length).toBe(3);
    // Mostra primeira e ultima data
    expect(screen.getByText("2026-01-01")).toBeInTheDocument();
    expect(screen.getByText("2026-03-01")).toBeInTheDocument();
  });
});
