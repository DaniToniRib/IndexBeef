import { useState } from "react";
import { post } from "../api/client";

interface Props {
  animalId: string;
  animalBrinco?: string;
  onVoltar: () => void;
}

// ---- Estilos reutilizáveis ----
const sCard: React.CSSProperties = {
  background: "#f9fafb",
  border: "1px solid #e5e7eb",
  borderRadius: 10,
  marginBottom: 16,
  overflow: "hidden",
};
const sHeader: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "12px 16px",
  cursor: "pointer",
  fontWeight: 600,
  fontSize: 15,
  userSelect: "none",
  background: "#f3f4f6",
  borderBottom: "1px solid #e5e7eb",
};
const sForm: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 12,
  padding: 20,
};
const sLabel: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  fontSize: 13,
  color: "#374151",
};
const sInput: React.CSSProperties = {
  padding: "6px 10px",
  border: "1px solid #d1d5db",
  borderRadius: 6,
  fontSize: 14,
  fontFamily: "system-ui, sans-serif",
};
const sBtnPrimary: React.CSSProperties = {
  padding: "8px 20px",
  background: "#059669",
  color: "white",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontWeight: 600,
  fontSize: 14,
  alignSelf: "flex-start",
};
const sMsgOk: React.CSSProperties = {
  background: "#d1fae5",
  color: "#065f46",
  padding: "10px 14px",
  borderRadius: 6,
  fontSize: 13,
};
const sMsgErro: React.CSSProperties = {
  background: "#fee2e2",
  color: "#991b1b",
  padding: "10px 14px",
  borderRadius: 6,
  fontSize: 13,
};
const sRow: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  gap: 12,
};

function hoje() {
  return new Date().toISOString().slice(0, 10);
}
function agora() {
  return new Date().toISOString().slice(0, 16);
}

// ---- Pesagem ----
function SecaoPesagem({ animalId }: { animalId: string }) {
  const [aberta, setAberta] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [ok, setOk] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [form, setForm] = useState({ data: hoje(), peso_kg: "", origem: "balanca" as "balanca" | "estimado" | "fita" });

  function campo(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setOk(null); setErro(null); setEnviando(true);
    try {
      await post("/pesagens", {
        animal_id: animalId,
        data: form.data,
        peso_kg: parseFloat(form.peso_kg),
        origem: form.origem,
      });
      setOk(`Pesagem registrada (${form.peso_kg} kg em ${form.data})`);
      setForm({ data: hoje(), peso_kg: "", origem: "balanca" });
    } catch (err) {
      setErro(String(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={sCard}>
      <div style={sHeader} onClick={() => setAberta((v) => !v)}>
        <span>{aberta ? "▼" : "▶"}</span> Pesagem
      </div>
      {aberta && (
        <form onSubmit={salvar} style={sForm}>
          <div style={sRow}>
            <label style={sLabel}>
              Data <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} type="date" value={form.data} onChange={campo("data")} />
            </label>
            <label style={sLabel}>
              Peso (kg) <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} type="number" step="0.1" min="0.1" value={form.peso_kg} onChange={campo("peso_kg")} />
            </label>
            <label style={sLabel}>
              Origem <span style={{ color: "#dc2626" }}>*</span>
              <select required style={sInput} value={form.origem} onChange={campo("origem")}>
                <option value="balanca">Balança</option>
                <option value="estimado">Estimado</option>
                <option value="fita">Fita</option>
              </select>
            </label>
          </div>
          {ok && <div style={sMsgOk}>{ok}</div>}
          {erro && <div style={sMsgErro}>Erro: {erro}</div>}
          <button type="submit" style={{ ...sBtnPrimary, opacity: enviando ? 0.6 : 1 }} disabled={enviando}>
            {enviando ? "Salvando…" : "Salvar"}
          </button>
        </form>
      )}
    </div>
  );
}

// ---- Aplicação Sanitária ----
function SecaoAplicacaoSanitaria({ animalId }: { animalId: string }) {
  const [aberta, setAberta] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [ok, setOk] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const inicial = {
    tipo: "vacina" as "vacina" | "vermifugo" | "terapeutico",
    data: hoje(), principio_ativo: "", nome_comercial: "",
    via: "IM" as "IM" | "SC" | "IV" | "oral" | "topico" | "outra",
    dose_ml: "", carencia_abate_dias: "", veterinario_crmv: "",
  };
  const [form, setForm] = useState(inicial);

  function campo(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setOk(null); setErro(null); setEnviando(true);
    try {
      const body: Record<string, unknown> = {
        animal_id: animalId,
        tipo: form.tipo,
        data: form.data,
        principio_ativo: form.principio_ativo,
        via: form.via,
      };
      if (form.nome_comercial) body.nome_comercial = form.nome_comercial;
      if (form.dose_ml) body.dose_ml = parseFloat(form.dose_ml);
      if (form.carencia_abate_dias) body.carencia_abate_dias = parseInt(form.carencia_abate_dias, 10);
      if (form.veterinario_crmv) body.veterinario_crmv = form.veterinario_crmv;
      await post("/aplicacoes-sanitarias", body);
      setOk("Aplicação sanitária registrada com sucesso!");
      setForm(inicial);
    } catch (err) {
      setErro(String(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={sCard}>
      <div style={sHeader} onClick={() => setAberta((v) => !v)}>
        <span>{aberta ? "▼" : "▶"}</span> Aplicação Sanitária
      </div>
      {aberta && (
        <form onSubmit={salvar} style={sForm}>
          <div style={sRow}>
            <label style={sLabel}>
              Tipo <span style={{ color: "#dc2626" }}>*</span>
              <select required style={sInput} value={form.tipo} onChange={campo("tipo")}>
                <option value="vacina">Vacina</option>
                <option value="vermifugo">Vermífugo</option>
                <option value="terapeutico">Terapêutico</option>
              </select>
            </label>
            <label style={sLabel}>
              Data <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} type="date" value={form.data} onChange={campo("data")} />
            </label>
          </div>
          <div style={sRow}>
            <label style={sLabel}>
              Princípio ativo <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} value={form.principio_ativo} onChange={campo("principio_ativo")} />
            </label>
            <label style={sLabel}>
              Nome comercial
              <input style={sInput} value={form.nome_comercial} onChange={campo("nome_comercial")} />
            </label>
          </div>
          <div style={sRow}>
            <label style={sLabel}>
              Via <span style={{ color: "#dc2626" }}>*</span>
              <select required style={sInput} value={form.via} onChange={campo("via")}>
                <option value="IM">IM (intramuscular)</option>
                <option value="SC">SC (subcutânea)</option>
                <option value="IV">IV (intravenosa)</option>
                <option value="oral">Oral</option>
                <option value="topico">Tópico</option>
                <option value="outra">Outra</option>
              </select>
            </label>
            <label style={sLabel}>
              Dose (ml)
              <input style={sInput} type="number" step="0.1" min="0" value={form.dose_ml} onChange={campo("dose_ml")} />
            </label>
            <label style={sLabel}>
              Carência abate (dias)
              <input style={sInput} type="number" min="0" value={form.carencia_abate_dias} onChange={campo("carencia_abate_dias")} />
            </label>
          </div>
          <label style={sLabel}>
            CRMV do veterinário
            <input style={sInput} value={form.veterinario_crmv} onChange={campo("veterinario_crmv")} />
          </label>
          {ok && <div style={sMsgOk}>{ok}</div>}
          {erro && <div style={sMsgErro}>Erro: {erro}</div>}
          <button type="submit" style={{ ...sBtnPrimary, opacity: enviando ? 0.6 : 1 }} disabled={enviando}>
            {enviando ? "Salvando…" : "Salvar"}
          </button>
        </form>
      )}
    </div>
  );
}

// ---- Atendimento Veterinário ----
function SecaoAtendimento({ animalId }: { animalId: string }) {
  const [aberta, setAberta] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [ok, setOk] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const inicial = {
    data_hora: agora(), veterinario_nome: "", veterinario_crmv: "",
    motivo: "", queixa: "", temperatura_c: "", diagnostico: "", observacoes: "",
  };
  const [form, setForm] = useState(inicial);

  function campo(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setOk(null); setErro(null); setEnviando(true);
    try {
      const body: Record<string, unknown> = {
        animal_id: animalId,
        data_hora: new Date(form.data_hora).toISOString(),
        veterinario_nome: form.veterinario_nome,
        veterinario_crmv: form.veterinario_crmv,
        motivo: form.motivo,
      };
      if (form.queixa) body.queixa = form.queixa;
      if (form.temperatura_c) body.temperatura_c = parseFloat(form.temperatura_c);
      if (form.diagnostico) body.diagnostico = form.diagnostico;
      if (form.observacoes) body.observacoes = form.observacoes;
      await post("/atendimentos-veterinarios", body);
      setOk("Atendimento veterinário registrado com sucesso!");
      setForm(inicial);
    } catch (err) {
      setErro(String(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={sCard}>
      <div style={sHeader} onClick={() => setAberta((v) => !v)}>
        <span>{aberta ? "▼" : "▶"}</span> Atendimento Veterinário
      </div>
      {aberta && (
        <form onSubmit={salvar} style={sForm}>
          <div style={sRow}>
            <label style={sLabel}>
              Data/hora <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} type="datetime-local" value={form.data_hora} onChange={campo("data_hora")} />
            </label>
            <label style={sLabel}>
              Temperatura (°C)
              <input style={sInput} type="number" step="0.1" value={form.temperatura_c} onChange={campo("temperatura_c")} />
            </label>
          </div>
          <div style={sRow}>
            <label style={sLabel}>
              Nome do veterinário <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} value={form.veterinario_nome} onChange={campo("veterinario_nome")} />
            </label>
            <label style={sLabel}>
              CRMV <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} value={form.veterinario_crmv} onChange={campo("veterinario_crmv")} />
            </label>
          </div>
          <label style={sLabel}>
            Motivo <span style={{ color: "#dc2626" }}>*</span>
            <input required style={sInput} value={form.motivo} onChange={campo("motivo")} />
          </label>
          <label style={sLabel}>
            Queixa principal
            <input style={sInput} value={form.queixa} onChange={campo("queixa")} />
          </label>
          <label style={sLabel}>
            Diagnóstico
            <input style={sInput} value={form.diagnostico} onChange={campo("diagnostico")} />
          </label>
          <label style={sLabel}>
            Observações
            <textarea
              style={{ ...sInput, resize: "vertical", minHeight: 72 }}
              value={form.observacoes}
              onChange={campo("observacoes")}
            />
          </label>
          {ok && <div style={sMsgOk}>{ok}</div>}
          {erro && <div style={sMsgErro}>Erro: {erro}</div>}
          <button type="submit" style={{ ...sBtnPrimary, opacity: enviando ? 0.6 : 1 }} disabled={enviando}>
            {enviando ? "Salvando…" : "Salvar"}
          </button>
        </form>
      )}
    </div>
  );
}

// ---- Evento Reprodutivo ----
type TipoEvento = "cobertura" | "iatf" | "diagnostico_gestacao" | "parto" | "aborto" | "desmama";

function SecaoEventoReprodutivo({ animalId }: { animalId: string }) {
  const [aberta, setAberta] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [ok, setOk] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const inicial = {
    tipo: "cobertura" as TipoEvento,
    data: hoje(), resultado: "", observacoes: "", peso_desmama_bezerro: "",
  };
  const [form, setForm] = useState(inicial);

  function campo(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setOk(null); setErro(null); setEnviando(true);
    try {
      const body: Record<string, unknown> = {
        animal_id: animalId,
        tipo: form.tipo,
        data: form.data,
      };
      if (form.resultado) body.resultado = form.resultado;
      if (form.observacoes) body.observacoes = form.observacoes;
      if (form.tipo === "desmama" && form.peso_desmama_bezerro)
        body.peso_desmama_bezerro = parseFloat(form.peso_desmama_bezerro);
      await post("/eventos-reprodutivos", body);
      setOk("Evento reprodutivo registrado com sucesso!");
      setForm(inicial);
    } catch (err) {
      setErro(String(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={sCard}>
      <div style={sHeader} onClick={() => setAberta((v) => !v)}>
        <span>{aberta ? "▼" : "▶"}</span> Evento Reprodutivo
      </div>
      {aberta && (
        <form onSubmit={salvar} style={sForm}>
          <div style={sRow}>
            <label style={sLabel}>
              Tipo <span style={{ color: "#dc2626" }}>*</span>
              <select required style={sInput} value={form.tipo} onChange={campo("tipo")}>
                <option value="cobertura">Cobertura</option>
                <option value="iatf">IATF</option>
                <option value="diagnostico_gestacao">Diagnóstico de gestação</option>
                <option value="parto">Parto</option>
                <option value="aborto">Aborto</option>
                <option value="desmama">Desmama</option>
              </select>
            </label>
            <label style={sLabel}>
              Data <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} type="date" value={form.data} onChange={campo("data")} />
            </label>
            <label style={sLabel}>
              Resultado
              <input style={sInput} value={form.resultado} onChange={campo("resultado")} placeholder="ex: Positivo" />
            </label>
          </div>
          {form.tipo === "desmama" && (
            <label style={sLabel}>
              Peso desmama do bezerro (kg)
              <input style={sInput} type="number" step="0.1" min="0" value={form.peso_desmama_bezerro} onChange={campo("peso_desmama_bezerro")} />
            </label>
          )}
          <label style={sLabel}>
            Observações
            <textarea
              style={{ ...sInput, resize: "vertical", minHeight: 72 }}
              value={form.observacoes}
              onChange={campo("observacoes")}
            />
          </label>
          {ok && <div style={sMsgOk}>{ok}</div>}
          {erro && <div style={sMsgErro}>Erro: {erro}</div>}
          <button type="submit" style={{ ...sBtnPrimary, opacity: enviando ? 0.6 : 1 }} disabled={enviando}>
            {enviando ? "Salvando…" : "Salvar"}
          </button>
        </form>
      )}
    </div>
  );
}

// ---- Exame Andrológico ----
function SecaoExameAndrologico({ animalId }: { animalId: string }) {
  const [aberta, setAberta] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [ok, setOk] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const inicial = {
    data: hoje(), perimetro_escrotal_cm: "",
    resultado: "" as "" | "apto" | "inapto" | "questionavel",
    veterinario: "", observacoes: "",
  };
  const [form, setForm] = useState(inicial);

  function campo(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setOk(null); setErro(null); setEnviando(true);
    try {
      const body: Record<string, unknown> = {
        animal_id: animalId,
        data: form.data,
      };
      if (form.perimetro_escrotal_cm) body.perimetro_escrotal_cm = parseFloat(form.perimetro_escrotal_cm);
      if (form.resultado) body.resultado = form.resultado;
      if (form.veterinario) body.veterinario = form.veterinario;
      if (form.observacoes) body.observacoes = form.observacoes;
      await post("/exames-andrologicos", body);
      setOk("Exame andrológico registrado com sucesso!");
      setForm(inicial);
    } catch (err) {
      setErro(String(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={sCard}>
      <div style={sHeader} onClick={() => setAberta((v) => !v)}>
        <span>{aberta ? "▼" : "▶"}</span> Exame Andrológico
      </div>
      {aberta && (
        <form onSubmit={salvar} style={sForm}>
          <div style={sRow}>
            <label style={sLabel}>
              Data <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} type="date" value={form.data} onChange={campo("data")} />
            </label>
            <label style={sLabel}>
              Perímetro escrotal (cm)
              <input style={sInput} type="number" step="0.1" min="0" value={form.perimetro_escrotal_cm} onChange={campo("perimetro_escrotal_cm")} />
            </label>
            <label style={sLabel}>
              Resultado
              <select style={sInput} value={form.resultado} onChange={campo("resultado")}>
                <option value="">(não informado)</option>
                <option value="apto">Apto</option>
                <option value="inapto">Inapto</option>
                <option value="questionavel">Questionável</option>
              </select>
            </label>
          </div>
          <label style={sLabel}>
            Veterinário responsável
            <input style={sInput} value={form.veterinario} onChange={campo("veterinario")} />
          </label>
          <label style={sLabel}>
            Observações
            <textarea
              style={{ ...sInput, resize: "vertical", minHeight: 72 }}
              value={form.observacoes}
              onChange={campo("observacoes")}
            />
          </label>
          {ok && <div style={sMsgOk}>{ok}</div>}
          {erro && <div style={sMsgErro}>Erro: {erro}</div>}
          <button type="submit" style={{ ...sBtnPrimary, opacity: enviando ? 0.6 : 1 }} disabled={enviando}>
            {enviando ? "Salvando…" : "Salvar"}
          </button>
        </form>
      )}
    </div>
  );
}

// ---- Página principal ----
export function LancamentosAnimal({ animalId, animalBrinco, onVoltar }: Props) {
  const titulo = animalBrinco ? `Lançamentos — Animal ${animalBrinco}` : "Lançamentos do animal";

  return (
    <section style={{ maxWidth: 860, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif", color: "#111827" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
        <button
          type="button"
          onClick={onVoltar}
          style={{ padding: "6px 14px", background: "none", border: "1px solid #d1d5db", borderRadius: 6, cursor: "pointer", fontSize: 13 }}
        >
          ← Voltar
        </button>
        <h2 style={{ margin: 0 }}>{titulo}</h2>
      </div>

      <SecaoPesagem animalId={animalId} />
      <SecaoAplicacaoSanitaria animalId={animalId} />
      <SecaoAtendimento animalId={animalId} />
      <SecaoEventoReprodutivo animalId={animalId} />
      <SecaoExameAndrologico animalId={animalId} />
    </section>
  );
}
