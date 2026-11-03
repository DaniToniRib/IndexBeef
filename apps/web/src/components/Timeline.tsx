import type {
  AplicacaoSanitaria,
  AtendimentoVeterinario,
  EventoGeofence,
  PesagemHistorico,
} from "../api/client";

interface Props {
  pesagens: readonly PesagemHistorico[];
  aplicacoes: readonly AplicacaoSanitaria[];
  atendimentos: readonly AtendimentoVeterinario[];
  eventos: readonly EventoGeofence[];
}

type Item = {
  ts: string;
  cor: string;
  rotulo: string;
  detalhe: string;
};

const CORES = {
  pesagem: "#059669",
  vacina: "#2563eb",
  vermifugo: "#7c3aed",
  terapeutico: "#dc2626",
  atendimento: "#f59e0b",
  entrada: "#10b981",
  saida: "#ef4444",
} as const;

export function Timeline({ pesagens, aplicacoes, atendimentos, eventos }: Props) {
  const itens: Item[] = [];

  for (const p of pesagens) {
    itens.push({
      ts: p.data,
      cor: CORES.pesagem,
      rotulo: "Pesagem",
      detalhe:
        `${Number(p.peso_kg).toFixed(1)} kg · origem: ${p.origem}` +
        (p.gmd_kg_dia !== null ? ` · GMD ${p.gmd_kg_dia.toFixed(2)}` : ""),
    });
  }

  for (const a of aplicacoes) {
    const cor =
      a.tipo === "vacina"
        ? CORES.vacina
        : a.tipo === "vermifugo"
          ? CORES.vermifugo
          : CORES.terapeutico;
    itens.push({
      ts: a.data,
      cor,
      rotulo: a.tipo.toUpperCase(),
      detalhe:
        `${a.principio_ativo}${a.nome_comercial ? ` (${a.nome_comercial})` : ""}` +
        (a.apto_abate_em ? ` · apto abate em ${a.apto_abate_em}` : "") +
        (a.veterinario_crmv ? ` · CRMV ${a.veterinario_crmv}` : ""),
    });
  }

  for (const at of atendimentos) {
    itens.push({
      ts: at.data_hora,
      cor: CORES.atendimento,
      rotulo: "Atendimento vet.",
      detalhe:
        `${at.motivo} · ${at.veterinario_nome} (CRMV ${at.veterinario_crmv})` +
        (at.diagnostico ? ` · dx: ${at.diagnostico}` : ""),
    });
  }

  for (const e of eventos) {
    itens.push({
      ts: e.timestamp,
      cor: e.tipo === "entrada" ? CORES.entrada : CORES.saida,
      rotulo: `Geofence · ${e.tipo}`,
      detalhe: `geofence ${e.geofence_id.slice(0, 8)}`,
    });
  }

  itens.sort((a, b) => (a.ts < b.ts ? 1 : -1));

  if (itens.length === 0) {
    return (
      <p style={{ color: "#6b7280" }}>
        Sem eventos registrados ainda para esse animal.
      </p>
    );
  }

  return (
    <ol
      style={{
        listStyle: "none",
        padding: 0,
        margin: 0,
        borderLeft: "2px solid #e5e7eb",
      }}
    >
      {itens.map((it, i) => (
        <li
          key={i}
          style={{
            position: "relative",
            padding: "8px 16px 8px 20px",
          }}
        >
          <span
            style={{
              position: "absolute",
              left: -7,
              top: 14,
              width: 12,
              height: 12,
              borderRadius: 6,
              background: it.cor,
              border: "2px solid white",
            }}
          />
          <div style={{ fontSize: 12, color: "#6b7280" }}>
            {it.ts.replace("T", " ").slice(0, 19)}
          </div>
          <div style={{ fontWeight: 600 }}>{it.rotulo}</div>
          <div style={{ fontSize: 14, color: "#374151" }}>{it.detalhe}</div>
        </li>
      ))}
    </ol>
  );
}
