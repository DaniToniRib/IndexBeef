import { useMemo, useState } from "react";
import { KeypointsCanvas } from "../components/KeypointsCanvas";
import { pontosIniciaisPadrao } from "../keypoint-utils";
import type { Keypoint } from "../types";

const LARGURA = 1280;
const ALTURA = 720;

export function RevisaoKeypoints() {
  const [frameUrl, setFrameUrl] = useState<string | undefined>(undefined);
  const [pontos, setPontos] = useState<Keypoint[]>(() => pontosIniciaisPadrao(LARGURA, ALTURA));

  const corrigidos = useMemo(() => pontos.filter((p) => p.corrigido).length, [pontos]);

  function escolherArquivo(ev: React.ChangeEvent<HTMLInputElement>) {
    const file = ev.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setFrameUrl(url);
  }

  function resetar() {
    setPontos(pontosIniciaisPadrao(LARGURA, ALTURA));
    if (frameUrl) {
      URL.revokeObjectURL(frameUrl);
      setFrameUrl(undefined);
    }
  }

  function copiarJson() {
    const payload = pontos.map((p) => ({
      id: p.id,
      x: Math.round(p.x),
      y: Math.round(p.y),
      corrigido: p.corrigido ?? false,
    }));
    navigator.clipboard?.writeText(JSON.stringify(payload, null, 2));
  }

  return (
    <section style={{ maxWidth: 1024, margin: "0 auto", padding: 24 }}>
      <h2 style={{ margin: "0 0 8px" }}>Revisao de keypoints laterais</h2>
      <p style={{ margin: "0 0 16px", color: "#6b7280" }}>
        18 pontos do docs/04. Arraste para corrigir. Pontos verdes foram corrigidos
        manualmente — essas correcoes viram dado de treino (ver docs/04 secao 6).
      </p>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", margin: "0 0 16px" }}>
        <input
          type="file"
          accept="image/*"
          onChange={escolherArquivo}
          aria-label="Carregar frame"
        />
        <button type="button" onClick={copiarJson}>
          Copiar JSON
        </button>
        <button type="button" onClick={resetar}>
          Reiniciar pontos
        </button>
        <span style={{ marginLeft: "auto", color: "#374151" }}>
          Corrigidos: <strong>{corrigidos}</strong> / {pontos.length}
        </span>
      </div>

      <KeypointsCanvas
        pontos={pontos}
        largura={LARGURA}
        altura={ALTURA}
        onChange={setPontos}
        frameUrl={frameUrl}
      />
    </section>
  );
}
