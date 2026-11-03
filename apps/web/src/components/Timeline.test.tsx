import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type {
  AplicacaoSanitaria,
  AtendimentoVeterinario,
  EventoGeofence,
  PesagemHistorico,
} from "../api/client";
import { Timeline } from "./Timeline";

const _pesagens: PesagemHistorico[] = [
  { id: "p1", data: "2026-01-01", peso_kg: "100", origem: "balanca", gmd_kg_dia: null },
  { id: "p2", data: "2026-02-01", peso_kg: "130", origem: "balanca", gmd_kg_dia: 0.97 },
];
const _aplicacoes: AplicacaoSanitaria[] = [
  {
    id: "a1",
    tipo: "vacina",
    data: "2026-01-15",
    principio_ativo: "Brucella abortus B19",
    via: "SC",
    carencia_abate_dias: null,
    veterinario_crmv: "SP-12345",
    apto_abate_em: null,
  },
];
const _atendimentos: AtendimentoVeterinario[] = [
  {
    id: "at1",
    data_hora: "2026-01-20T10:00:00Z",
    veterinario_nome: "Dra. Souza",
    veterinario_crmv: "MS-98765",
    motivo: "clinico",
    diagnostico: "febre leve",
  },
];
const _eventos: EventoGeofence[] = [
  {
    id: "e1",
    geofence_id: "11111111-1111-1111-1111-111111111111",
    tipo: "saida",
    timestamp: "2026-02-05T06:30:00Z",
  },
];

describe("<Timeline />", () => {
  it("mostra 'sem eventos' quando tudo vazio", () => {
    render(
      <Timeline pesagens={[]} aplicacoes={[]} atendimentos={[]} eventos={[]} />,
    );
    expect(screen.getByText(/sem eventos/i)).toBeInTheDocument();
  });

  it("ordena do mais recente ao mais antigo", () => {
    const { container } = render(
      <Timeline
        pesagens={_pesagens}
        aplicacoes={_aplicacoes}
        atendimentos={_atendimentos}
        eventos={_eventos}
      />,
    );
    const items = Array.from(container.querySelectorAll("li"));
    expect(items.length).toBe(5); // 2 pesagens + 1 vacina + 1 atendimento + 1 geofence
    // Primeiro item = evento mais recente (2026-02-05 saida)
    expect(items[0].textContent).toContain("saida");
  });

  it("rotulos cobrem todos os tipos", () => {
    render(
      <Timeline
        pesagens={_pesagens.slice(0, 1)}
        aplicacoes={_aplicacoes}
        atendimentos={_atendimentos}
        eventos={_eventos}
      />,
    );
    expect(screen.getByText("Pesagem")).toBeInTheDocument();
    expect(screen.getByText("VACINA")).toBeInTheDocument();
    expect(screen.getByText("Atendimento vet.")).toBeInTheDocument();
    expect(screen.getByText(/Geofence · saida/)).toBeInTheDocument();
  });
});
