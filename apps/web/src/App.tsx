import { useState } from "react";
import { RevisaoKeypoints } from "./pages/RevisaoKeypoints";

type Tela = "home" | "revisao-keypoints";

export function App() {
  const [tela, setTela] = useState<Tela>("home");

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", color: "#111827" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "12px 24px",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <strong style={{ fontSize: 18 }}>🐂 IndexBeef</strong>
        <nav style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            onClick={() => setTela("home")}
            aria-current={tela === "home" ? "page" : undefined}
          >
            Inicio
          </button>
          <button
            type="button"
            onClick={() => setTela("revisao-keypoints")}
            aria-current={tela === "revisao-keypoints" ? "page" : undefined}
          >
            Revisao de keypoints
          </button>
        </nav>
      </header>

      {tela === "home" ? (
        <main style={{ maxWidth: 1024, margin: "0 auto", padding: 24 }}>
          <h1>IndexBeef</h1>
          <p>Fase 0 — estrutura inicial. Avaliacao morfologica de bovinos Nelore.</p>
          <p>
            Acesse <em>Revisao de keypoints</em> para experimentar a tela do docs/04.
          </p>
        </main>
      ) : (
        <RevisaoKeypoints />
      )}
    </div>
  );
}
