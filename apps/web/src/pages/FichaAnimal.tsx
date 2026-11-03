import { useEffect, useState } from "react";
import {
  get,
  type Animal,
  type AnimalHistorico,
  type AplicacaoSanitaria,
  type AtendimentoVeterinario,
  type EventoGeofence,
  type Fazenda,
} from "../api/client";
import { GraficoPeso } from "../components/GraficoPeso";
import { Timeline } from "../components/Timeline";

export function FichaAnimal() {
  const [fazendas, setFazendas] = useState<Fazenda[]>([]);
  const [fazendaId, setFazendaId] = useState<string>("");
  const [animais, setAnimais] = useState<Animal[]>([]);
  const [animalId, setAnimalId] = useState<string>("");

  const [animal, setAnimal] = useState<Animal | null>(null);
  const [historico, setHistorico] = useState<AnimalHistorico | null>(null);
  const [aplicacoes, setAplicacoes] = useState<AplicacaoSanitaria[]>([]);
  const [atendimentos, setAtendimentos] = useState<AtendimentoVeterinario[]>([]);
  const [eventos, setEventos] = useState<EventoGeofence[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState<boolean>(false);

  useEffect(() => {
    get<Fazenda[]>("/fazendas").then(setFazendas).catch((e) => setErro(String(e)));
  }, []);

  useEffect(() => {
    if (!fazendaId) {
      setAnimais([]);
      return;
    }
    get<Animal[]>(`/animais?fazenda_id=${fazendaId}`).then(setAnimais).catch(
      (e) => setErro(String(e)),
    );
  }, [fazendaId]);

  useEffect(() => {
    if (!animalId) {
      setAnimal(null);
      setHistorico(null);
      setAplicacoes([]);
      setAtendimentos([]);
      setEventos([]);
      return;
    }
    setCarregando(true);
    setErro(null);
    Promise.all([
      get<Animal>(`/animais/${animalId}`),
      get<AnimalHistorico>(`/animais/${animalId}/historico`),
      get<AplicacaoSanitaria[]>(`/aplicacoes-sanitarias?animal_id=${animalId}`),
      get<AtendimentoVeterinario[]>(
        `/atendimentos-veterinarios?animal_id=${animalId}`,
      ),
      get<EventoGeofence[]>(`/animais/${animalId}/eventos-geofence`),
    ])
      .then(([a, h, ap, at, ev]) => {
        setAnimal(a);
        setHistorico(h);
        setAplicacoes(ap);
        setAtendimentos(at);
        setEventos(ev);
      })
      .catch((e) => setErro(String(e)))
      .finally(() => setCarregando(false));
  }, [animalId]);

  return (
    <section style={{ maxWidth: 1024, margin: "0 auto", padding: 24 }}>
      <h2 style={{ margin: "0 0 16px" }}>Ficha do animal</h2>

      <div
        style={{
          display: "flex",
          gap: 12,
          flexWrap: "wrap",
          marginBottom: 24,
          padding: 12,
          background: "#f9fafb",
          borderRadius: 8,
        }}
      >
        <label>
          Fazenda:{" "}
          <select
            value={fazendaId}
            onChange={(e) => {
              setFazendaId(e.target.value);
              setAnimalId("");
            }}
          >
            <option value="">(selecione)</option>
            {fazendas.map((f) => (
              <option key={f.id} value={f.id}>
                {f.nome} — {f.tipo}
              </option>
            ))}
          </select>
        </label>
        <label>
          Animal:{" "}
          <select
            value={animalId}
            onChange={(e) => setAnimalId(e.target.value)}
            disabled={!fazendaId}
          >
            <option value="">(selecione)</option>
            {animais.map((a) => (
              <option key={a.id} value={a.id}>
                {a.brinco ?? "(sem brinco)"} · {a.sexo} ·{" "}
                {a.rgn ?? "sem RGN"}
              </option>
            ))}
          </select>
        </label>
      </div>

      {erro ? (
        <div
          style={{
            background: "#fee2e2",
            color: "#991b1b",
            padding: 12,
            borderRadius: 8,
            marginBottom: 16,
          }}
        >
          Erro: {erro}
        </div>
      ) : null}

      {carregando ? <p>Carregando…</p> : null}

      {animal && historico ? (
        <>
          <section
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
              gap: 12,
              marginBottom: 24,
            }}
          >
            <Cartao
              rotulo="Brinco"
              valor={animal.brinco ?? "—"}
              sub={animal.rgn ?? ""}
            />
            <Cartao rotulo="Sexo" valor={animal.sexo} />
            <Cartao
              rotulo="Idade"
              valor={
                historico.idade_meses !== null
                  ? `${historico.idade_meses.toFixed(1)} meses`
                  : "—"
              }
              sub={
                historico.idade_dias !== null
                  ? `${historico.idade_dias} dias`
                  : ""
              }
            />
            <Cartao
              rotulo="Peso atual"
              valor={
                historico.peso_atual_kg !== null
                  ? `${Number(historico.peso_atual_kg).toFixed(1)} kg`
                  : "—"
              }
            />
            <Cartao
              rotulo="GMD total"
              valor={
                historico.gmd_total_kg_dia !== null
                  ? `${historico.gmd_total_kg_dia.toFixed(2)} kg/dia`
                  : "—"
              }
            />
            <Cartao
              rotulo="Situacao"
              valor={animal.situacao}
              sub={animal.ceip ? "CEIP ✓" : ""}
            />
          </section>

          <h3 style={{ margin: "24px 0 8px" }}>Evolucao de peso</h3>
          <GraficoPeso pesagens={historico.pesagens} />

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

function Cartao({
  rotulo,
  valor,
  sub,
}: {
  rotulo: string;
  valor: string;
  sub?: string;
}) {
  return (
    <div
      style={{
        padding: 12,
        background: "#f9fafb",
        borderRadius: 8,
        border: "1px solid #e5e7eb",
      }}
    >
      <div style={{ fontSize: 12, color: "#6b7280" }}>{rotulo}</div>
      <div style={{ fontSize: 18, fontWeight: 600 }}>{valor}</div>
      {sub ? <div style={{ fontSize: 12, color: "#9ca3af" }}>{sub}</div> : null}
    </div>
  );
}
