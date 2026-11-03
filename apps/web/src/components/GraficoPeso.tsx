import type { PesagemHistorico } from "../api/client";

interface Props {
  pesagens: readonly PesagemHistorico[];
  largura?: number;
  altura?: number;
}

/**
 * Grafico de linha SVG puro, sem lib externa.
 * Eixo x = data (igualmente espacado por indice), eixo y = peso_kg.
 */
export function GraficoPeso({ pesagens, largura = 720, altura = 240 }: Props) {
  if (pesagens.length < 1) {
    return (
      <div style={{ color: "#6b7280", padding: 24 }}>
        Sem pesagens para plotar.
      </div>
    );
  }

  const padding = { top: 16, right: 24, bottom: 32, left: 48 };
  const w = largura - padding.left - padding.right;
  const h = altura - padding.top - padding.bottom;

  const pesos = pesagens.map((p) => Number(p.peso_kg));
  const pesoMin = Math.min(...pesos);
  const pesoMax = Math.max(...pesos);
  const yRange = Math.max(1, pesoMax - pesoMin);
  const n = pesagens.length;

  const xStep = n > 1 ? w / (n - 1) : 0;

  const pontos = pesagens.map((p, i) => {
    const x = padding.left + (n > 1 ? i * xStep : w / 2);
    const y = padding.top + h - ((Number(p.peso_kg) - pesoMin) / yRange) * h;
    return { x, y, p };
  });

  const pathLinha = pontos
    .map((pt, i) => `${i === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`)
    .join(" ");

  // Grid y com 4 linhas horizontais
  const linhasGrid = Array.from({ length: 4 }, (_, i) => {
    const t = i / 3;
    const y = padding.top + h - t * h;
    const peso = pesoMin + t * yRange;
    return { y, peso };
  });

  return (
    <svg
      role="img"
      aria-label="Grafico de peso do animal"
      viewBox={`0 0 ${largura} ${altura}`}
      style={{
        width: "100%",
        maxWidth: largura,
        background: "#f9fafb",
        borderRadius: 8,
        display: "block",
      }}
    >
      {linhasGrid.map((g) => (
        <g key={g.y}>
          <line
            x1={padding.left}
            x2={largura - padding.right}
            y1={g.y}
            y2={g.y}
            stroke="#e5e7eb"
            strokeDasharray="2 2"
          />
          <text
            x={padding.left - 8}
            y={g.y + 4}
            fill="#6b7280"
            fontSize={11}
            textAnchor="end"
          >
            {g.peso.toFixed(0)} kg
          </text>
        </g>
      ))}

      <path d={pathLinha} fill="none" stroke="#059669" strokeWidth={2} />

      {pontos.map((pt) => (
        <g key={pt.p.id}>
          <circle cx={pt.x} cy={pt.y} r={4} fill="#059669" />
          <title>
            {pt.p.data} · {Number(pt.p.peso_kg).toFixed(1)} kg
            {pt.p.gmd_kg_dia !== null
              ? ` · GMD ${pt.p.gmd_kg_dia.toFixed(2)} kg/dia`
              : ""}
          </title>
        </g>
      ))}

      {/* eixo x: primeira e ultima data */}
      <text
        x={padding.left}
        y={altura - 10}
        fill="#6b7280"
        fontSize={11}
      >
        {pesagens[0].data}
      </text>
      {n > 1 ? (
        <text
          x={largura - padding.right}
          y={altura - 10}
          fill="#6b7280"
          fontSize={11}
          textAnchor="end"
        >
          {pesagens[n - 1].data}
        </text>
      ) : null}
    </svg>
  );
}
