import type { Avaliacao } from "../api/client";

interface Props {
  avaliacao: Avaliacao;
}

const STATUS_COR: Record<string, string> = {
  concluida: "#059669",
  processando: "#f59e0b",
  erro: "#dc2626",
  revisar: "#7c3aed",
  capturada: "#6b7280",
};

const STATUS_LABEL: Record<string, string> = {
  concluida: "Concluída",
  processando: "Processando...",
  erro: "Erro",
  revisar: "Revisar",
  capturada: "Capturada",
};

const MEDIDAS_EXIBIR: Array<[keyof NonNullable<Avaliacao["medida"]>, string, string]> = [
  ["altura_cernelha_cm", "Altura cernelha", "cm"],
  ["altura_garupa_cm", "Altura garupa", "cm"],
  ["comprimento_corporal_cm", "Comprimento corporal", "cm"],
  ["profundidade_toracica_cm", "Profundidade torácica", "cm"],
  ["comprimento_garupa_cm", "Comprimento garupa", "cm"],
  ["largura_garupa_cm", "Largura garupa", "cm"],
  ["altura_cupim_cm", "Altura cupim", "cm"],
  ["umbigo_chao_cm", "Umbigo ao chão", "cm"],
  ["perimetro_toracico_est_cm", "Perímetro torácico", "cm"],
  ["inclinacao_garupa_graus", "Inclinação garupa", "°"],
  ["jarrete_graus", "Ângulo jarrete", "°"],
];

const TIPO_LABEL: Record<string, string> = {
  peso_atual: "Peso atual",
  peso_18m: "18 meses",
  peso_24m: "24 meses",
  peso_30m: "30 meses",
};

function fmt(v: number | null | undefined, d = 1, suf = ""): string {
  if (v == null) return "—";
  return `${Number(v).toFixed(d)}${suf}`;
}

export function AvaliacaoResultado({ avaliacao }: Props) {
  const cor = STATUS_COR[avaliacao.status] ?? "#6b7280";
  const label = STATUS_LABEL[avaliacao.status] ?? avaliacao.status;

  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        overflow: "hidden",
        marginBottom: 12,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "10px 14px",
          background: "#f9fafb",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <span style={{ fontSize: 13, color: "#374151" }}>
          {new Date(avaliacao.data_hora).toLocaleString("pt-BR")}
          {avaliacao.versao_pipeline ? ` · v${avaliacao.versao_pipeline}` : ""}
        </span>
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: cor,
            background: `${cor}18`,
            padding: "2px 10px",
            borderRadius: 12,
          }}
        >
          {label}
        </span>
      </div>

      {avaliacao.status === "processando" && (
        <div style={{ padding: "12px 14px", color: "#92400e" }}>
          Processando… recarregue em alguns segundos.
        </div>
      )}

      {avaliacao.status === "erro" && (
        <div style={{ padding: "12px 14px", color: "#991b1b" }}>
          {avaliacao.observacoes ?? "Erro no pipeline."}
        </div>
      )}

      {avaliacao.status === "concluida" && avaliacao.medida && (
        <div style={{ padding: 14, display: "flex", flexWrap: "wrap", gap: 20 }}>
          {/* Medidas */}
          <div style={{ flex: "1 1 260px" }}>
            <div style={{ fontWeight: 600, marginBottom: 8, color: "#111827" }}>
              Medidas
            </div>
            <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 13 }}>
              <tbody>
                {MEDIDAS_EXIBIR.map(([campo, nome, unidade]) => {
                  const v = avaliacao.medida![campo];
                  if (v == null) return null;
                  return (
                    <tr key={campo}>
                      <td style={{ color: "#6b7280", padding: "2px 0", paddingRight: 12 }}>
                        {nome}
                      </td>
                      <td style={{ fontWeight: 500 }}>
                        {fmt(Number(v), 1, ` ${unidade}`)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Caixa virtual */}
          {avaliacao.caixa_virtual && (
            <div style={{ flex: "1 1 200px" }}>
              <div style={{ fontWeight: 600, marginBottom: 8, color: "#111827" }}>
                Caixa virtual
              </div>
              <table style={{ borderCollapse: "collapse", fontSize: 13 }}>
                <tbody>
                  {[
                    ["C", avaliacao.caixa_virtual.c_cm, "cm"],
                    ["P", avaliacao.caixa_virtual.p_cm, "cm"],
                    ["L", avaliacao.caixa_virtual.l_cm, "cm"],
                    ["Volume", avaliacao.caixa_virtual.volume_l, "L"],
                    ["IPL", avaliacao.caixa_virtual.ipl, ""],
                    ["Compacidade", avaliacao.caixa_virtual.compacidade, ""],
                    ["Índ. comprimento", avaliacao.caixa_virtual.indice_comprimento, ""],
                  ].map(([k, v, u]) =>
                    v != null ? (
                      <tr key={String(k)}>
                        <td style={{ color: "#6b7280", paddingRight: 12, padding: "2px 12px 2px 0" }}>
                          {k}
                        </td>
                        <td style={{ fontWeight: 500 }}>{fmt(Number(v), 2, u ? ` ${u}` : "")}</td>
                      </tr>
                    ) : null,
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Predições e projeção */}
          {avaliacao.predicoes && avaliacao.predicoes.length > 0 && (
            <div style={{ flex: "1 1 240px" }}>
              <div style={{ fontWeight: 600, marginBottom: 8, color: "#111827" }}>
                Peso e projeção
              </div>
              <table style={{ borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: "left", color: "#6b7280", fontWeight: 400, paddingRight: 12, paddingBottom: 4 }}>
                      Projeção
                    </th>
                    <th style={{ textAlign: "right", color: "#6b7280", fontWeight: 400, paddingRight: 8 }}>
                      kg
                    </th>
                    <th style={{ textAlign: "right", color: "#6b7280", fontWeight: 400 }}>
                      faixa
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {avaliacao.predicoes.map((pred) => (
                    <tr key={pred.tipo}>
                      <td style={{ paddingRight: 12, padding: "2px 12px 2px 0" }}>
                        {TIPO_LABEL[pred.tipo] ?? pred.tipo}
                      </td>
                      <td style={{ fontWeight: 600, textAlign: "right", paddingRight: 8 }}>
                        {fmt(pred.valor, 1)}
                      </td>
                      <td style={{ fontSize: 11, color: "#6b7280", textAlign: "right" }}>
                        {pred.faixa_min != null && pred.faixa_max != null
                          ? `${fmt(pred.faixa_min, 0)}–${fmt(pred.faixa_max, 0)}`
                          : ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
