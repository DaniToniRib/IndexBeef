import { useState } from "react";
import { FichaAnimal } from "./pages/FichaAnimal";
import { RevisaoKeypoints } from "./pages/RevisaoKeypoints";

type Tela = "home" | "revisao-keypoints" | "ficha-animal";

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
            onClick={() => setTela("ficha-animal")}
            aria-current={tela === "ficha-animal" ? "page" : undefined}
          >
            Ficha do animal
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
          <p>Avaliacao morfologica de bovinos Nelore + gestao de pecuaria.</p>
          <ul>
            <li>
              <strong>Ficha do animal</strong> — timeline unificada: pesagens,
              aplicacoes sanitarias, atendimentos vet e eventos de geofence.
            </li>
            <li>
              <strong>Revisao de keypoints</strong> — 18 pontos do docs/04 para
              revisao da avaliacao morfologica.
            </li>
          </ul>
        </main>
      ) : tela === "ficha-animal" ? (
        <FichaAnimal />
      ) : (
        <RevisaoKeypoints />
      )}
    </div>
  );
}
