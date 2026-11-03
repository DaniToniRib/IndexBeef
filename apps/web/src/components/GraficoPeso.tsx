import type { PesagemHistorico, ProjecaoPonto } from "../api/client";

interface Props {
  pesagens: readonly PesagemHistorico[];
  projecao?: ProjecaoPonto[];
  nascimento?: string;
  largura?: number;
  altura?: number;
}

/**
 * Grafico de linha SVG puro, sem lib externa.
 * Eixo x = data (igualmente espacado por indice), eixo y = peso_kg.
 * Opcional: linha tracejada de projecao Brody com banda de intervalo.
 */
export function GraficoPeso({ pesagens, projecao, nascimento, largura = 720, altura = 260 }: Props) {
  const temProjecao = projecao && projecao.length > 0 && nascimento;

  if (pesagens.length < 1 && !temProjecao) {
    return (
      <div style={{ color: "#6b7280", padding: 24 }}>
        Sem pesagens para plotar.
      </div>
    );
  }

  const padding = { top: 36, right: 24, bottom: 32, left: 52 };
  const w = largura - padding.left - padding.right;
  const h = altura - padding.top - padding.bottom;

  // Converter pesagens para pontos {ms, peso}
  const ptHistorico = pesagens.map((p) => ({
    ms: new Date(p.data).getTime(),
    peso: Number(p.peso_kg),
    label: `${p.data} · ${Number(p.peso_kg).toFixed(1)} kg${p.gmd_kg_dia !== null ? ` · GMD ${p.gmd_kg_dia.toFixed(2)} kg/dia` : ""}`,
    id: p.id,
  }));

  // Converter projecao para pontos {ms, peso, min, max}
  const nascimentoMs = temProjecao ? new Date(nascimento!).getTime() : 0;
  const ptProjecao = temProjecao
    ? projecao!.map((pt) => ({
        ms: nascimentoMs + pt.idade_meses * 30.44 * 86400000,
        peso: pt.peso_kg,
        min: pt.peso_min_kg,
        max: pt.peso_max_kg,
      }))
    : [];

  // Eixo X: range de datas
  const todosMs = [
    ...ptHistorico.map((p) => p.ms),
    ...ptProjecao.map((p) => p.ms),
  ];
  const msMin = Math.min(...todosMs);
  const msMax = Math.max(...todosMs);
  const msRange = Math.max(1, msMax - msMin);

  // Eixo Y: range de pesos
  const todosPesos = [
    ...ptHistorico.map((p) => p.peso),
    ...ptProjecao.flatMap((p) => [p.peso, p.min, p.max]),
  ];
  const pesoMin = todosPesos.length > 0 ? Math.min(...todosPesos) : 0;
  const pesoMax = todosPesos.length > 0 ? Math.max(...todosPesos) : 100;
  const yRange = Math.max(1, pesoMax - pesoMin);

  function xOf(ms: number) {
    return padding.left + ((ms - msMin) / msRange) * w;
  }
  function yOf(peso: number) {
    return padding.top + h - ((peso - pesoMin) / yRange) * h;
  }

  // Polyline historico
  const pathHistorico = ptHistorico
    .map((pt, i) => `${i === 0 ? "M" : "L"} ${xOf(pt.ms).toFixed(1)} ${yOf(pt.peso).toFixed(1)}`)
    .join(" ");

  // Polyline projecao (linha tracejada)
  const pathProjecao = ptProjecao
    .map((pt, i) => `${i === 0 ? "M" : "L"} ${xOf(pt.ms).toFixed(1)} ${yOf(pt.peso).toFixed(1)}`)
    .join(" ");

  // Poligono de banda min/max
  const bandaPoints = temProjecao
    ? [
        ...ptProjecao.map((pt) => `${xOf(pt.ms).toFixed(1)},${yOf(pt.max).toFixed(1)}`),
        ...[...ptProjecao].reverse().map((pt) => `${xOf(pt.ms).toFixed(1)},${yOf(pt.min).toFixed(1)}`),
      ].join(" ")
    : "";

  // Grid y com 4 linhas horizontais
  const linhasGrid = Array.from({ length: 4 }, (_, i) => {
    const t = i / 3;
    const y = padding.top + h - t * h;
    const peso = pesoMin + t * yRange;
    return { y, peso };
  });

  // Labels eixo X
  const formatarData = (ms: number) =>
    new Date(ms).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "2-digit" });

  return (
    <div>
      {temProjecao && (
        <div
          style={{
            display: "flex",
            gap: 16,
            justifyContent: "flex-end",
            marginBottom: 6,
            fontSize: 12,
            color: "#374151",
          }}
        >
          <span>
            <svg width="14" height="14" style={{ verticalAlign: "middle", marginRight: 4 }}>
              <circle cx="7" cy="7" r="5" fill="#059669" />
            </svg>
            Pesagens reais
          </span>
          <span>
            <svg width="14" height="14" style={{ verticalAlign: "middle", marginRight: 4 }}>
              <circle cx="7" cy="7" r="5" fill="none" stroke="#3b82f6" strokeWidth="1.5" />
            </svg>
            Projeção Brody
          </span>
        </div>
      )}
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

        {/* Banda de intervalo de projecao */}
        {temProjecao && ptProjecao.length > 1 && (
          <polygon
            points={bandaPoints}
            fill="#3b82f620"
          />
        )}

        {/* Linha de historico */}
        {ptHistorico.length > 1 && (
          <path d={pathHistorico} fill="none" stroke="#059669" strokeWidth={2} />
        )}

        {/* Linha de projecao tracejada */}
        {temProjecao && ptProjecao.length > 1 && (
          <path
            d={pathProjecao}
            fill="none"
            stroke="#3b82f6"
            strokeWidth={2}
            strokeDasharray="6 3"
          />
        )}

        {/* Pontos historicos */}
        {ptHistorico.map((pt) => (
          <g key={pt.id}>
            <circle cx={xOf(pt.ms)} cy={yOf(pt.peso)} r={4} fill="#059669" />
            <title>{pt.label}</title>
          </g>
        ))}

        {/* Pontos de projecao (circulo vazio) */}
        {temProjecao &&
          ptProjecao.map((pt, i) => (
            <g key={i}>
              <circle
                cx={xOf(pt.ms)}
                cy={yOf(pt.peso)}
                r={4}
                fill="white"
                stroke="#3b82f6"
                strokeWidth={1.5}
              />
              <title>
                {formatarData(pt.ms)} · proj. {pt.peso.toFixed(1)} kg (intervalo {pt.min.toFixed(1)}–{pt.max.toFixed(1)} kg)
              </title>
            </g>
          ))}

        {/* Eixo X: primeira e ultima data */}
        <text x={padding.left} y={altura - 10} fill="#6b7280" fontSize={11}>
          {formatarData(msMin)}
        </text>
        <text
          x={largura - padding.right}
          y={altura - 10}
          fill="#6b7280"
          fontSize={11}
          textAnchor="end"
        >
          {formatarData(msMax)}
        </text>
      </svg>
    </div>
  );
}
