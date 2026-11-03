import { useEffect, useState } from "react";
import { get, type Dashboard, type DashboardGeofence, type Fazenda } from "../api/client";

export function DashboardFazenda() {
  const [fazendas, setFazendas] = useState<Fazenda[]>([]);
  const [fazendaId, setFazendaId] = useState("");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    get<Fazenda[]>("/fazendas").then(setFazendas).catch((e) => setErro(String(e)));
  }, []);

  useEffect(() => {
    if (!fazendaId) { setDashboard(null); return; }
    setCarregando(true);
    setErro(null);
    get<Dashboard>(`/fazendas/${fazendaId}/dashboard`)
      .then(setDashboard)
      .catch((e) => setErro(String(e)))
      .finally(() => setCarregando(false));
  }, [fazendaId]);

  return (
    <section style={{ maxWidth: 1024, margin: "0 auto", padding: 24 }}>
      <h2 style={{ margin: "0 0 16px" }}>Dashboard da fazenda</h2>

      <div style={{ marginBottom: 20 }}>
        <label>
          Fazenda:{" "}
          <select value={fazendaId} onChange={(e) => setFazendaId(e.target.value)}>
            <option value="">(selecione)</option>
            {fazendas.map((f) => (
              <option key={f.id} value={f.id}>{f.nome} — {f.tipo}</option>
            ))}
          </select>
        </label>
      </div>

      {erro && (
        <div style={{ background: "#fee2e2", color: "#991b1b", padding: 12, borderRadius: 8, marginBottom: 16 }}>
          Erro: {erro}
        </div>
      )}

      {carregando && <p>Carregando…</p>}

      {dashboard && (
        <>
          {/* Cards de totais */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 24 }}>
            <StatCard rotulo="Animais" valor={String(dashboard.total_animais)} />
            <StatCard
              rotulo="Por sexo"
              valor={Object.entries(dashboard.animais_por_sexo)
                .map(([k, v]) => `${k}: ${v}`)
                .join(" · ") || "—"}
            />
            <StatCard rotulo="Campanhas ativas" valor={String(dashboard.campanhas_ativas)} />
            <StatCard rotulo="Pesagens (7d)" valor={String(dashboard.pesagens_recentes_7d)} />
            <StatCard rotulo="Avaliações (7d)" valor={String(dashboard.avaliacoes_semana)} />
            <StatCard
              rotulo="Alertas bateria"
              valor={String(dashboard.alertas_bateria.length)}
              destaque={dashboard.alertas_bateria.length > 0 ? "#dc2626" : undefined}
            />
            <StatCard
              rotulo="Fora da cerca"
              valor={String(dashboard.animais_fora_cerca.length)}
              destaque={dashboard.animais_fora_cerca.length > 0 ? "#f59e0b" : undefined}
            />
          </div>

          {/* Alertas de bateria */}
          {dashboard.alertas_bateria.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ margin: "0 0 8px", color: "#dc2626" }}>Alertas de bateria baixa</h3>
              <div style={{ border: "1px solid #fecaca", borderRadius: 8, overflow: "hidden" }}>
                {dashboard.alertas_bateria.map((al) => (
                  <div
                    key={al.dispositivo_id}
                    style={{ padding: "8px 14px", borderBottom: "1px solid #fecaca", fontSize: 13, background: "#fff5f5" }}
                  >
                    <strong>{al.bateria_pct}%</strong> · {al.dispositivo_modelo ?? "dispositivo"}{" "}
                    {al.animal_brinco ? `· animal ${al.animal_brinco}` : ""}{" "}
                    <span style={{ color: "#6b7280" }}>
                      {new Date(al.timestamp).toLocaleString("pt-BR")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Animais fora da cerca */}
          {dashboard.animais_fora_cerca.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ margin: "0 0 8px", color: "#b45309" }}>Animais fora da cerca</h3>
              <div style={{ border: "1px solid #fde68a", borderRadius: 8, overflow: "hidden" }}>
                {dashboard.animais_fora_cerca.map((af) => (
                  <div
                    key={af.animal_id}
                    style={{ padding: "8px 14px", borderBottom: "1px solid #fde68a", fontSize: 13, background: "#fffbeb" }}
                  >
                    Animal <strong>{af.animal_brinco ?? af.animal_id.slice(0, 8)}</strong>
                    {" · "}saiu de <strong>{af.geofence_nome ?? af.geofence_id.slice(0, 8)}</strong>
                    {" "}em{" "}
                    <span style={{ color: "#6b7280" }}>
                      {new Date(af.saida_em).toLocaleString("pt-BR")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mapa de geofences SVG */}
          {dashboard.geofences.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ margin: "0 0 8px" }}>Geofences ativas</h3>
              <MapaGeofences geofences={dashboard.geofences} />
            </div>
          )}
        </>
      )}
    </section>
  );
}

function StatCard({ rotulo, valor, destaque }: { rotulo: string; valor: string; destaque?: string }) {
  return (
    <div style={{ padding: 12, background: "#f9fafb", borderRadius: 8, border: `1px solid ${destaque ?? "#e5e7eb"}` }}>
      <div style={{ fontSize: 12, color: "#6b7280" }}>{rotulo}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: destaque ?? "#111827" }}>{valor}</div>
    </div>
  );
}

function MapaGeofences({ geofences }: { geofences: DashboardGeofence[] }) {
  const TIPO_COR: Record<string, string> = {
    pasto: "#059669", limite: "#1e40af", alerta: "#dc2626", curral: "#7c3aed",
  };

  type Poly = { pts: [number, number][]; nome: string; tipo: string };
  const polys: Poly[] = [];

  for (const gf of geofences) {
    const match = gf.poligono_wkt.match(/POLYGON\s*\(\(([^)]+)\)/i);
    if (!match) continue;
    const pts: [number, number][] = match[1]
      .split(",")
      .map((s) => {
        const [lng, lat] = s.trim().split(/\s+/).map(Number);
        return [lng, lat] as [number, number];
      })
      .filter((p) => !p.some(isNaN));
    if (pts.length >= 3) polys.push({ pts, nome: gf.nome, tipo: gf.tipo });
  }

  if (polys.length === 0) return <p style={{ color: "#6b7280" }}>WKT sem polígonos válidos.</p>;

  const allX = polys.flatMap((p) => p.pts.map((pt) => pt[0]));
  const allY = polys.flatMap((p) => p.pts.map((pt) => pt[1]));
  const minX = Math.min(...allX), maxX = Math.max(...allX);
  const minY = Math.min(...allY), maxY = Math.max(...allY);
  const dx = maxX - minX || 1, dy = maxY - minY || 1;

  const W = 640, H = 360, PAD = 24;
  const toSvg = ([x, y]: [number, number]): [number, number] => [
    PAD + ((x - minX) / dx) * (W - 2 * PAD),
    H - PAD - ((y - minY) / dy) * (H - 2 * PAD),
  ];

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      style={{ width: "100%", maxWidth: W, background: "#f0fdf4", borderRadius: 8, display: "block" }}
    >
      {polys.map((poly, i) => {
        const svgPts = poly.pts.map(toSvg);
        const d = svgPts.map(([x, y], j) => `${j === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`).join(" ") + " Z";
        const cor = TIPO_COR[poly.tipo] ?? "#6b7280";
        const [cx, cy] = svgPts.reduce(
          ([ax, ay], [x, y]) => [ax + x / svgPts.length, ay + y / svgPts.length],
          [0, 0],
        );
        return (
          <g key={i}>
            <path d={d} fill={`${cor}30`} stroke={cor} strokeWidth={1.5} />
            <text x={cx} y={cy} fontSize={10} fill={cor} textAnchor="middle" dominantBaseline="middle">
              {poly.nome}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
