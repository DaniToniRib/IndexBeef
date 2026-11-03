/**
 * PainelRemoto — visao simplificada para o criador acompanhar a fazenda remotamente.
 * Consome GET /fazendas/{fazenda_id}/painel-remoto (Fase 5).
 */
import { useState } from "react";

interface Fazenda {
  id: string;
  nome: string;
  municipio: string | null;
  uf: string | null;
}

interface Totais {
  animais: number;
  lotes: number;
}

interface UltimaAvaliacao {
  animal_brinco: string | null;
  data: string;
  peso_estimado_kg: number | null;
  indice_garrote: number | null;
}

interface AlertaEcc {
  animal_brinco: string | null;
  data: string | null;
  ecc: number | null;
}

interface PesoMedioLote {
  lote_nome: string;
  categoria: string;
  peso_medio_kg: number | null;
  n_animais: number;
}

interface DadosPainel {
  fazenda: Fazenda;
  totais: Totais;
  ultimas_avaliacoes: UltimaAvaliacao[];
  alertas_ecc: AlertaEcc[];
  peso_medio_lote: PesoMedioLote[];
}

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function formatarData(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR", {
      dateStyle: "short",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export function PainelRemoto() {
  const [fazendaId, setFazendaId] = useState("");
  const [dados, setDados] = useState<DadosPainel | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function carregar() {
    const id = fazendaId.trim();
    if (!id) {
      setErro("Informe o ID da fazenda.");
      return;
    }
    setCarregando(true);
    setErro(null);
    setDados(null);
    try {
      const resp = await fetch(`${API_BASE}/fazendas/${id}/painel-remoto`);
      if (resp.status === 404) {
        setErro("Fazenda não encontrada.");
        return;
      }
      if (!resp.ok) {
        setErro(`Erro ${resp.status}: ${resp.statusText}`);
        return;
      }
      const json = (await resp.json()) as DadosPainel;
      setDados(json);
    } catch (e) {
      setErro(`Falha de conexão: ${String(e)}`);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <main style={{ maxWidth: 1024, margin: "0 auto", padding: 24 }}>
      <h2 style={{ marginBottom: 16 }}>Painel Remoto</h2>

      {/* Busca por ID de fazenda */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        <input
          type="text"
          value={fazendaId}
          onChange={(e) => setFazendaId(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && carregar()}
          placeholder="UUID da fazenda"
          style={{
            flex: 1,
            padding: "8px 12px",
            border: "1px solid #d1d5db",
            borderRadius: 6,
            fontSize: 14,
          }}
        />
        <button
          type="button"
          onClick={carregar}
          disabled={carregando}
          style={{
            padding: "8px 20px",
            background: "#059669",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            cursor: carregando ? "not-allowed" : "pointer",
            fontSize: 14,
          }}
        >
          {carregando ? "Carregando..." : "Carregar"}
        </button>
      </div>

      {/* Erro */}
      {erro && (
        <div
          style={{
            padding: 12,
            background: "#fef2f2",
            border: "1px solid #fca5a5",
            borderRadius: 6,
            color: "#dc2626",
            marginBottom: 16,
          }}
        >
          {erro}
        </div>
      )}

      {/* Resultado */}
      {dados && (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Cabeçalho da fazenda */}
          <section>
            <h3 style={{ marginBottom: 4 }}>{dados.fazenda.nome}</h3>
            {dados.fazenda.municipio && (
              <p style={{ margin: 0, color: "#6b7280", fontSize: 14 }}>
                {dados.fazenda.municipio}
                {dados.fazenda.uf ? ` / ${dados.fazenda.uf}` : ""}
              </p>
            )}
          </section>

          {/* Cards de totais */}
          <section>
            <h4 style={{ marginBottom: 12 }}>Totais</h4>
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
              <div
                style={{
                  flex: "1 1 140px",
                  padding: 16,
                  background: "#ecfdf5",
                  borderRadius: 8,
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: 32, fontWeight: 700, color: "#059669" }}>
                  {dados.totais.animais}
                </div>
                <div style={{ fontSize: 13, color: "#374151", marginTop: 4 }}>Animais</div>
              </div>
              <div
                style={{
                  flex: "1 1 140px",
                  padding: 16,
                  background: "#eff6ff",
                  borderRadius: 8,
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: 32, fontWeight: 700, color: "#2563eb" }}>
                  {dados.totais.lotes}
                </div>
                <div style={{ fontSize: 13, color: "#374151", marginTop: 4 }}>Lotes</div>
              </div>
            </div>
          </section>

          {/* Últimas avaliações */}
          <section>
            <h4 style={{ marginBottom: 12 }}>Últimas Avaliações</h4>
            {dados.ultimas_avaliacoes.length === 0 ? (
              <p style={{ color: "#9ca3af", fontSize: 14 }}>Nenhuma avaliação encontrada.</p>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: 14,
                  }}
                >
                  <thead>
                    <tr style={{ background: "#f9fafb" }}>
                      <th style={thStyle}>Brinco</th>
                      <th style={thStyle}>Data</th>
                      <th style={thStyle}>Peso estimado (kg)</th>
                      <th style={thStyle}>Índice Garrote</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.ultimas_avaliacoes.map((av, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid #f3f4f6" }}>
                        <td style={tdStyle}>{av.animal_brinco ?? "—"}</td>
                        <td style={tdStyle}>{formatarData(av.data)}</td>
                        <td style={tdStyle}>
                          {av.peso_estimado_kg != null
                            ? av.peso_estimado_kg.toFixed(1)
                            : "—"}
                        </td>
                        <td style={tdStyle}>
                          {av.indice_garrote != null
                            ? av.indice_garrote.toFixed(2)
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Alertas ECC */}
          <section>
            <h4 style={{ marginBottom: 12, color: "#dc2626" }}>
              Alertas ECC ({dados.alertas_ecc.length})
            </h4>
            {dados.alertas_ecc.length === 0 ? (
              <p style={{ color: "#9ca3af", fontSize: 14 }}>Nenhum alerta de ECC.</p>
            ) : (
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {dados.alertas_ecc.map((alerta, i) => (
                  <li
                    key={i}
                    style={{
                      padding: "8px 12px",
                      marginBottom: 4,
                      background: "#fef2f2",
                      border: "1px solid #fca5a5",
                      borderRadius: 6,
                      color: "#dc2626",
                      fontSize: 14,
                    }}
                  >
                    <strong>{alerta.animal_brinco ?? "—"}</strong> — ECC{" "}
                    {alerta.ecc != null ? alerta.ecc.toFixed(1) : "?"} em{" "}
                    {formatarData(alerta.data)}
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Peso médio por lote */}
          <section>
            <h4 style={{ marginBottom: 12 }}>Peso Médio por Lote</h4>
            {dados.peso_medio_lote.length === 0 ? (
              <p style={{ color: "#9ca3af", fontSize: 14 }}>
                Nenhum lote com pesagem nos últimos 90 dias.
              </p>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: 14,
                  }}
                >
                  <thead>
                    <tr style={{ background: "#f9fafb" }}>
                      <th style={thStyle}>Lote</th>
                      <th style={thStyle}>Categoria</th>
                      <th style={thStyle}>Peso médio (kg)</th>
                      <th style={thStyle}>N animais</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.peso_medio_lote.map((lote, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid #f3f4f6" }}>
                        <td style={tdStyle}>{lote.lote_nome}</td>
                        <td style={tdStyle}>{lote.categoria}</td>
                        <td style={tdStyle}>
                          {lote.peso_medio_kg != null
                            ? lote.peso_medio_kg.toFixed(1)
                            : "—"}
                        </td>
                        <td style={tdStyle}>{lote.n_animais}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}
    </main>
  );
}

const thStyle: React.CSSProperties = {
  padding: "8px 12px",
  textAlign: "left",
  fontWeight: 600,
  borderBottom: "2px solid #e5e7eb",
  whiteSpace: "nowrap",
};

const tdStyle: React.CSSProperties = {
  padding: "8px 12px",
  color: "#374151",
};
