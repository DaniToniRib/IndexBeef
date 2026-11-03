import { useEffect, useRef, useState } from "react";
import {
  API_URL,
  get,
  getBlob,
  type Animal,
  type AnimalHistorico,
  type AplicacaoSanitaria,
  type AtendimentoVeterinario,
  type Avaliacao,
  type AvaliacaoListItem,
  type EventoGeofence,
  type Fazenda,
  type PredicaoAvaliacao,
} from "../api/client";
import { AvaliacaoResultado } from "../components/AvaliacaoResultado";
import { GraficoPeso } from "../components/GraficoPeso";
import { Timeline } from "../components/Timeline";

interface Props {
  onNovaAvaliacao: (animalId: string) => void;
}

export function FichaAnimal({ onNovaAvaliacao }: Props) {
  const [fazendas, setFazendas] = useState<Fazenda[]>([]);
  const [fazendaId, setFazendaId] = useState<string>("");
  const [animais, setAnimais] = useState<Animal[]>([]);
  const [animalId, setAnimalId] = useState<string>("");

  const [animal, setAnimal] = useState<Animal | null>(null);
  const [historico, setHistorico] = useState<AnimalHistorico | null>(null);
  const [aplicacoes, setAplicacoes] = useState<AplicacaoSanitaria[]>([]);
  const [atendimentos, setAtendimentos] = useState<AtendimentoVeterinario[]>([]);
  const [eventos, setEventos] = useState<EventoGeofence[]>([]);
  const [avaliacoes, setAvaliacoes] = useState<AvaliacaoListItem[]>([]);
  const [avaliacaoDetalhe, setAvaliacaoDetalhe] = useState<Avaliacao | null>(null);

  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [baixandoPdf, setBaixandoPdf] = useState(false);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    get<Fazenda[]>("/fazendas").then(setFazendas).catch((e) => setErro(String(e)));
  }, []);

  useEffect(() => {
    if (!fazendaId) { setAnimais([]); return; }
    get<Animal[]>(`/animais?fazenda_id=${fazendaId}`).then(setAnimais).catch(
      (e) => setErro(String(e)),
    );
  }, [fazendaId]);

  useEffect(() => {
    if (!animalId) {
      setAnimal(null); setHistorico(null); setAplicacoes([]);
      setAtendimentos([]); setEventos([]); setAvaliacoes([]);
      setAvaliacaoDetalhe(null);
      return;
    }
    setCarregando(true);
    setErro(null);
    Promise.all([
      get<Animal>(`/animais/${animalId}`),
      get<AnimalHistorico>(`/animais/${animalId}/historico`),
      get<AplicacaoSanitaria[]>(`/aplicacoes-sanitarias?animal_id=${animalId}`),
      get<AtendimentoVeterinario[]>(`/atendimentos-veterinarios?animal_id=${animalId}`),
      get<EventoGeofence[]>(`/animais/${animalId}/eventos-geofence`),
      get<AvaliacaoListItem[]>(`/animais/${animalId}/avaliacoes`),
    ])
      .then(([a, h, ap, at, ev, avs]) => {
        setAnimal(a); setHistorico(h); setAplicacoes(ap);
        setAtendimentos(at); setEventos(ev); setAvaliacoes(avs);
      })
      .catch((e) => setErro(String(e)))
      .finally(() => setCarregando(false));
  }, [animalId]);

  // Polling para avaliacoes "processando"
  useEffect(() => {
    const temProcessando = avaliacoes.some((a) => a.status === "processando");
    if (temProcessando && !pollingRef.current) {
      pollingRef.current = setInterval(() => {
        get<AvaliacaoListItem[]>(`/animais/${animalId}/avaliacoes`).then((avs) => {
          setAvaliacoes(avs);
          if (!avs.some((a) => a.status === "processando")) {
            if (pollingRef.current) clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
        }).catch(() => {});
      }, 3000);
    } else if (!temProcessando && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    return () => {
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
    };
  }, [avaliacoes, animalId]);

  async function abrirAvaliacao(id: string) {
    try {
      const av = await get<Avaliacao>(`/avaliacoes/${id}`);
      setAvaliacaoDetalhe(av);
    } catch (e) {
      setErro(String(e));
    }
  }

  async function baixarPdf() {
    if (!animalId) return;
    setBaixandoPdf(true);
    try {
      const blob = await getBlob(`/animais/${animalId}/relatorio`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ficha-${animal?.brinco ?? animalId.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErro(String(e));
    } finally {
      setBaixandoPdf(false);
    }
  }

  return (
    <section style={{ maxWidth: 1024, margin: "0 auto", padding: 24 }}>
      <h2 style={{ margin: "0 0 16px" }}>Ficha do animal</h2>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 24, padding: 12, background: "#f9fafb", borderRadius: 8 }}>
        <label>
          Fazenda:{" "}
          <select value={fazendaId} onChange={(e) => { setFazendaId(e.target.value); setAnimalId(""); }}>
            <option value="">(selecione)</option>
            {fazendas.map((f) => (
              <option key={f.id} value={f.id}>{f.nome} — {f.tipo}</option>
            ))}
          </select>
        </label>
        <label>
          Animal:{" "}
          <select value={animalId} onChange={(e) => setAnimalId(e.target.value)} disabled={!fazendaId}>
            <option value="">(selecione)</option>
            {animais.map((a) => (
              <option key={a.id} value={a.id}>
                {a.brinco ?? "(sem brinco)"} · {a.sexo} · {a.rgn ?? "sem RGN"}
              </option>
            ))}
          </select>
        </label>

        {animalId && (
          <>
            <button
              type="button"
              onClick={() => onNovaAvaliacao(animalId)}
              style={{ padding: "4px 14px", background: "#059669", color: "white", border: "none", borderRadius: 6, cursor: "pointer", fontWeight: 600 }}
            >
              + Nova avaliação
            </button>
            <button
              type="button"
              onClick={baixarPdf}
              disabled={baixandoPdf}
              style={{ padding: "4px 14px", background: "#1e40af", color: "white", border: "none", borderRadius: 6, cursor: baixandoPdf ? "default" : "pointer" }}
            >
              {baixandoPdf ? "Gerando PDF…" : "Exportar PDF"}
            </button>
          </>
        )}
      </div>

      {erro ? (
        <div style={{ background: "#fee2e2", color: "#991b1b", padding: 12, borderRadius: 8, marginBottom: 16 }}>
          Erro: {erro}
        </div>
      ) : null}

      {carregando ? <p>Carregando…</p> : null}

      {animal && historico ? (
        <>
          <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 24 }}>
            <Cartao rotulo="Brinco" valor={animal.brinco ?? "—"} sub={animal.rgn ?? ""} />
            <Cartao rotulo="Sexo" valor={animal.sexo} />
            <Cartao
              rotulo="Idade"
              valor={historico.idade_meses !== null ? `${historico.idade_meses.toFixed(1)} meses` : "—"}
              sub={historico.idade_dias !== null ? `${historico.idade_dias} dias` : ""}
            />
            <Cartao
              rotulo="Peso atual"
              valor={historico.peso_atual_kg !== null ? `${Number(historico.peso_atual_kg).toFixed(1)} kg` : "—"}
            />
            <Cartao
              rotulo="GMD total"
              valor={historico.gmd_total_kg_dia !== null ? `${historico.gmd_total_kg_dia.toFixed(2)} kg/dia` : "—"}
            />
            <Cartao rotulo="Situacao" valor={animal.situacao} sub={animal.ceip ? "CEIP ✓" : ""} />
          </section>

          <h3 style={{ margin: "24px 0 8px" }}>Evolucao de peso</h3>
          <GraficoPeso pesagens={historico.pesagens} />

          {/* Avaliações morfológicas */}
          <h3 style={{ margin: "24px 0 8px" }}>Avaliações morfológicas</h3>
          {avaliacoes.length === 0 ? (
            <p style={{ color: "#6b7280" }}>Nenhuma avaliação registrada. Use "+ Nova avaliação" para iniciar.</p>
          ) : (
            <div style={{ marginBottom: 16 }}>
              {avaliacoes.map((av) => (
                <div
                  key={av.id}
                  style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 12px", borderBottom: "1px solid #e5e7eb", cursor: "pointer" }}
                  onClick={() => abrirAvaliacao(av.id)}
                >
                  <span style={{ fontSize: 13, color: "#374151", flex: 1 }}>
                    {new Date(av.data_hora).toLocaleString("pt-BR")}
                    {av.versao_pipeline ? ` · v${av.versao_pipeline}` : ""}
                  </span>
                  <StatusChip status={av.status} />
                </div>
              ))}
            </div>
          )}

          {avaliacaoDetalhe && (
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <strong style={{ fontSize: 14 }}>Detalhe da avaliação</strong>
                <button type="button" style={{ fontSize: 12 }} onClick={() => setAvaliacaoDetalhe(null)}>Fechar</button>
              </div>
              <AvaliacaoResultado avaliacao={avaliacaoDetalhe} />
              <IndicesCards predicoes={avaliacaoDetalhe.predicoes ?? []} />
            </div>
          )}

          <h3 style={{ margin: "24px 0 8px" }}>Timeline</h3>
          <Timeline
            pesagens={historico.pesagens}
            aplicacoes={aplicacoes}
            atendimentos={atendimentos}
            eventos={eventos}
          />
        </>
      ) : null}
    </section>
  );
}

function Cartao({ rotulo, valor, sub }: { rotulo: string; valor: string; sub?: string }) {
  return (
    <div style={{ padding: 12, background: "#f9fafb", borderRadius: 8, border: "1px solid #e5e7eb" }}>
      <div style={{ fontSize: 12, color: "#6b7280" }}>{rotulo}</div>
      <div style={{ fontSize: 18, fontWeight: 600 }}>{valor}</div>
      {sub ? <div style={{ fontSize: 12, color: "#9ca3af" }}>{sub}</div> : null}
    </div>
  );
}

const STATUS_COR: Record<string, string> = {
  concluida: "#059669", processando: "#f59e0b", erro: "#dc2626",
  revisar: "#7c3aed", capturada: "#6b7280",
};
const STATUS_LABEL: Record<string, string> = {
  concluida: "Concluída", processando: "Processando", erro: "Erro",
  revisar: "Revisar", capturada: "Capturada",
};

function StatusChip({ status }: { status: string }) {
  const cor = STATUS_COR[status] ?? "#6b7280";
  return (
    <span style={{
      fontSize: 11, fontWeight: 600, color: cor,
      background: `${cor}18`, padding: "2px 10px", borderRadius: 10,
    }}>
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

const INDICE_LABEL: Record<string, string> = {
  indice_garrote: "Indice Garrote",
  indice_reprodutor: "Indice Reprodutor",
  indice_matriz: "Indice Matriz",
};

function IndicesCards({ predicoes }: { predicoes: PredicaoAvaliacao[] }) {
  const indices = predicoes.filter((p) =>
    ["indice_garrote", "indice_reprodutor", "indice_matriz"].includes(p.tipo),
  );
  if (indices.length === 0) return null;
  return (
    <div style={{ marginTop: 16 }}>
      <strong style={{ fontSize: 13, color: "#374151" }}>Indices de Aptidao</strong>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 8 }}>
        {indices.map((idx) => (
          <div
            key={idx.tipo}
            style={{
              padding: 12, background: "#f0fdf4", borderRadius: 8,
              border: "1px solid #bbf7d0", minWidth: 160,
            }}
          >
            <div style={{ fontSize: 12, color: "#166534", fontWeight: 600, marginBottom: 4 }}>
              {INDICE_LABEL[idx.tipo] ?? idx.tipo}
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#15803d" }}>
              {idx.valor !== null && idx.valor !== undefined ? Number(idx.valor).toFixed(1) : "—"}
            </div>
            {idx.explicacao && idx.explicacao.length > 0 && (
              <ul style={{ margin: "6px 0 0", padding: "0 0 0 14px", fontSize: 11, color: "#4b5563" }}>
                {idx.explicacao.slice(0, 3).map((c) => (
                  <li key={c.componente}>
                    {c.componente}: {c.contribuicao_pct.toFixed(1)}%
                  </li>
                ))}
              </ul>
            )}
            <div style={{ marginTop: 6, fontSize: 10, color: "#9ca3af" }}>
              Recomendacao de triagem — confirme com avaliacao tecnica.
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
