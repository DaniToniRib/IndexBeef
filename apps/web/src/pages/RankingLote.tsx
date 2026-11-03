import { useEffect, useState } from "react";
import { get } from "../api/client";

interface RankingItem {
  animal_id: string;
  brinco: string | null;
  nome: string | null;
  valor: number;
  posicao: number;
  confianca: number | null;
}

interface RankingResponse {
  total: number;
  itens: RankingItem[];
}

interface Props {
  loteId: string;
}

const INDICES = [
  { value: "garrote", label: "Garrote" },
  { value: "reprodutor", label: "Reprodutor" },
  { value: "matriz", label: "Matriz" },
];

export function RankingLote({ loteId }: Props) {
  const [indice, setIndice] = useState("garrote");
  const [ranking, setRanking] = useState<RankingResponse | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    if (!loteId) return;
    setCarregando(true);
    setErro(null);
    get<RankingResponse>(`/lotes/${loteId}/ranking?indice=${indice}`)
      .then(setRanking)
      .catch((e) => setErro(String(e)))
      .finally(() => setCarregando(false));
  }, [loteId, indice]);

  return (
    <section style={{ maxWidth: 800, margin: "0 auto", padding: 24 }}>
      <h2 style={{ margin: "0 0 16px" }}>Ranking do Lote</h2>

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16 }}>
        <label style={{ fontSize: 13 }}>
          Indice:{" "}
          <select value={indice} onChange={(e) => setIndice(e.target.value)}>
            {INDICES.map((i) => (
              <option key={i.value} value={i.value}>{i.label}</option>
            ))}
          </select>
        </label>
        {ranking && (
          <span style={{ fontSize: 13, color: "#6b7280" }}>
            {ranking.total} {ranking.total === 1 ? "animal" : "animais"}
          </span>
        )}
      </div>

      {erro && (
        <div style={{ padding: 12, background: "#fee2e2", color: "#991b1b", borderRadius: 8, marginBottom: 16 }}>
          {erro}
        </div>
      )}

      {carregando && <p style={{ color: "#6b7280" }}>Carregando ranking…</p>}

      {!carregando && ranking && ranking.itens.length === 0 && (
        <div style={{ padding: 16, background: "#f9fafb", borderRadius: 8, color: "#6b7280", textAlign: "center" }}>
          Nenhum animal com indice calculado neste lote.<br />
          Use "Calcular indices" em cada avaliacao para popular o ranking.
        </div>
      )}

      {!carregando && ranking && ranking.itens.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
          <thead>
            <tr style={{ background: "#f9fafb", borderBottom: "2px solid #e5e7eb" }}>
              <th style={{ padding: "8px 12px", textAlign: "left", fontWeight: 600 }}>Pos.</th>
              <th style={{ padding: "8px 12px", textAlign: "left", fontWeight: 600 }}>Brinco</th>
              <th style={{ padding: "8px 12px", textAlign: "right", fontWeight: 600 }}>Valor (0-100)</th>
              <th style={{ padding: "8px 12px", textAlign: "left", fontWeight: 600 }}>Barra</th>
            </tr>
          </thead>
          <tbody>
            {ranking.itens.map((item) => (
              <tr
                key={item.animal_id}
                style={{ borderBottom: "1px solid #f3f4f6" }}
              >
                <td style={{ padding: "8px 12px", color: "#6b7280", fontWeight: 600, width: 48 }}>
                  {item.posicao}
                </td>
                <td style={{ padding: "8px 12px" }}>
                  {item.brinco ?? item.animal_id.slice(0, 8)}
                </td>
                <td style={{ padding: "8px 12px", textAlign: "right", fontWeight: 600 }}>
                  {item.valor.toFixed(1)}
                </td>
                <td style={{ padding: "8px 12px", width: 180 }}>
                  <div style={{ background: "#e5e7eb", borderRadius: 4, height: 10, position: "relative" }}>
                    <div
                      style={{
                        position: "absolute", left: 0, top: 0, bottom: 0,
                        width: `${Math.min(item.valor, 100)}%`,
                        background: item.valor >= 60 ? "#059669" : item.valor >= 35 ? "#f59e0b" : "#dc2626",
                        borderRadius: 4,
                      }}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
