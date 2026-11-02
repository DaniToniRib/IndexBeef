import { useRef, useState, type PointerEvent } from "react";
import { NOMES_KEYPOINTS, type Keypoint, type KeypointId } from "../types";
import { moverPara } from "../keypoint-utils";

interface Props {
  pontos: readonly Keypoint[];
  largura: number;
  altura: number;
  onChange: (pontos: Keypoint[]) => void;
  frameUrl?: string;
  raio?: number;
}

export function KeypointsCanvas({
  pontos,
  largura,
  altura,
  onChange,
  frameUrl,
  raio = 10,
}: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [arrastando, setArrastando] = useState<KeypointId | null>(null);
  const [hover, setHover] = useState<KeypointId | null>(null);

  function paraCoordSvg(ev: PointerEvent<SVGSVGElement>): { x: number; y: number } {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const rect = svg.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return { x: 0, y: 0 };
    // Converte px na tela para coord do viewBox (0..largura, 0..altura).
    const x = ((ev.clientX - rect.left) / rect.width) * largura;
    const y = ((ev.clientY - rect.top) / rect.height) * altura;
    return { x, y };
  }

  function iniciarArraste(id: KeypointId, ev: PointerEvent<SVGCircleElement>) {
    ev.stopPropagation();
    (ev.target as SVGCircleElement).setPointerCapture(ev.pointerId);
    setArrastando(id);
  }

  function moverArraste(ev: PointerEvent<SVGSVGElement>) {
    if (arrastando === null) return;
    const { x, y } = paraCoordSvg(ev);
    onChange(moverPara(pontos, arrastando, x, y, largura, altura));
  }

  function terminarArraste(ev: PointerEvent<SVGSVGElement>) {
    if (arrastando !== null) {
      (ev.target as Element).releasePointerCapture?.(ev.pointerId);
    }
    setArrastando(null);
  }

  return (
    <svg
      ref={svgRef}
      role="img"
      aria-label="Revisao de keypoints laterais"
      viewBox={`0 0 ${largura} ${altura}`}
      style={{
        width: "100%",
        maxWidth: 900,
        aspectRatio: `${largura} / ${altura}`,
        background: "#111827",
        touchAction: "none",
        display: "block",
        borderRadius: 8,
      }}
      onPointerMove={moverArraste}
      onPointerUp={terminarArraste}
      onPointerLeave={terminarArraste}
    >
      {frameUrl ? (
        <image href={frameUrl} x={0} y={0} width={largura} height={altura} preserveAspectRatio="xMidYMid meet" />
      ) : (
        <>
          <rect x={0} y={0} width={largura} height={altura} fill="#1f2937" />
          <text
            x={largura / 2}
            y={altura / 2}
            fill="#6b7280"
            fontSize={14}
            textAnchor="middle"
          >
            frame placeholder — carregue uma imagem da avaliacao
          </text>
        </>
      )}

      {pontos.map((p) => {
        const nome = NOMES_KEYPOINTS[p.id];
        const ativo = hover === p.id || arrastando === p.id;
        return (
          <g key={p.id}>
            <circle
              data-testid={`kp-${p.id}`}
              cx={p.x}
              cy={p.y}
              r={ativo ? raio + 3 : raio}
              fill={p.corrigido ? "#22c55e" : "#f59e0b"}
              stroke="#111827"
              strokeWidth={2}
              style={{ cursor: "grab" }}
              onPointerDown={(ev) => iniciarArraste(p.id, ev)}
              onPointerEnter={() => setHover(p.id)}
              onPointerLeave={() => setHover((prev) => (prev === p.id ? null : prev))}
            />
            {ativo ? (
              <g pointerEvents="none">
                <rect
                  x={p.x + raio + 6}
                  y={p.y - 10}
                  width={Math.max(80, nome.length * 7)}
                  height={20}
                  rx={4}
                  fill="rgba(17,24,39,0.9)"
                />
                <text
                  x={p.x + raio + 12}
                  y={p.y + 4}
                  fill="#e5e7eb"
                  fontSize={12}
                  fontFamily="system-ui, sans-serif"
                >
                  {p.id} · {nome}
                </text>
              </g>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}
