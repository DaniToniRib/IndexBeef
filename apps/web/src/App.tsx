import { useState } from "react";
import { DashboardFazenda } from "./pages/DashboardFazenda";
import { FichaAnimal } from "./pages/FichaAnimal";
import { NovaAvaliacao } from "./pages/NovaAvaliacao";
import { RevisaoKeypoints } from "./pages/RevisaoKeypoints";

type Tela =
  | "home"
  | "revisao-keypoints"
  | "ficha-animal"
  | { tipo: "nova-avaliacao"; animalId: string }
  | "dashboard";

export function App() {
  const [tela, setTela] = useState<Tela>("home");

  const telaAtiva = typeof tela === "string" ? tela : tela.tipo;

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
          {(
            [
              ["home", "Inicio"],
              ["ficha-animal", "Ficha do animal"],
              ["dashboard", "Dashboard"],
              ["revisao-keypoints", "Revisao de keypoints"],
            ] as const
          ).map(([chave, rotulo]) => (
            <button
              key={chave}
              type="button"
              onClick={() => setTela(chave)}
              aria-current={telaAtiva === chave ? "page" : undefined}
              style={{
                fontWeight: telaAtiva === chave ? 700 : undefined,
                borderBottom: telaAtiva === chave ? "2px solid #059669" : "2px solid transparent",
              }}
            >
              {rotulo}
            </button>
          ))}
        </nav>
      </header>

      {tela === "home" ? (
        <main style={{ maxWidth: 1024, margin: "0 auto", padding: 24 }}>
          <h1>IndexBeef</h1>
          <p>Avaliacao morfologica de bovinos Nelore + gestao de pecuaria.</p>
          <ul>
            <li>
              <strong>Ficha do animal</strong> — timeline unificada, avaliações morfológicas e exportação PDF.
            </li>
            <li>
              <strong>Dashboard</strong> — totais, alertas de bateria, animais fora da cerca e mapa de geofences.
            </li>
            <li>
              <strong>Revisao de keypoints</strong> — 18 pontos do docs/04.
            </li>
          </ul>
        </main>
      ) : tela === "ficha-animal" ? (
        <FichaAnimal
          onNovaAvaliacao={(animalId) => setTela({ tipo: "nova-avaliacao", animalId })}
        />
      ) : tela === "dashboard" ? (
        <DashboardFazenda />
      ) : telaAtiva === "nova-avaliacao" ? (
        <NovaAvaliacao
          animalIdInicial={typeof tela === "object" ? tela.animalId : undefined}
          onConcluido={() => setTela("ficha-animal")}
          onCancelar={() => setTela("ficha-animal")}
        />
      ) : (
        <RevisaoKeypoints />
      )}
    </div>
  );
}
