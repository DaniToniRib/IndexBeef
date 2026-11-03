import { useEffect, useState } from "react";
import { get, post, type Fazenda, type Lote } from "../api/client";

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
  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
  gap: 12,
};

// ---- Seção de Fazenda ----
function SecaoFazenda() {
  const [aberta, setAberta] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [ok, setOk] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const inicial = {
    nome: "", tipo: "fazenda" as const, municipio: "", uf: "", bioma: "",
    latitude: "", longitude: "", area_hectares: "", codigo_sisbov: "", inscricao_estadual: "",
  };
  const [form, setForm] = useState(inicial);

  function campo(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const val = key === "uf" ? e.target.value.toUpperCase().slice(0, 2) : e.target.value;
      setForm((f) => ({ ...f, [key]: val }));
    };
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setOk(null); setErro(null); setEnviando(true);
    try {
      const body: Record<string, unknown> = { nome: form.nome, tipo: form.tipo };
      if (form.municipio) body.municipio = form.municipio;
      if (form.uf) body.uf = form.uf;
      if (form.bioma) body.bioma = form.bioma;
      if (form.latitude) body.latitude = parseFloat(form.latitude);
      if (form.longitude) body.longitude = parseFloat(form.longitude);
      if (form.area_hectares) body.area_hectares = parseFloat(form.area_hectares);
      if (form.codigo_sisbov) body.codigo_sisbov = form.codigo_sisbov;
      if (form.inscricao_estadual) body.inscricao_estadual = form.inscricao_estadual;
      await post("/fazendas", body);
      setOk("Fazenda criada com sucesso!");
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
        <span>{aberta ? "▼" : "▶"}</span> Nova Fazenda
      </div>
      {aberta && (
        <form onSubmit={salvar} style={sForm}>
          <div style={sRow}>
            <label style={sLabel}>
              Nome <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} value={form.nome} onChange={campo("nome")} />
            </label>
            <label style={sLabel}>
              Tipo <span style={{ color: "#dc2626" }}>*</span>
              <select required style={sInput} value={form.tipo} onChange={campo("tipo")}>
                <option value="fazenda">Fazenda</option>
                <option value="sitio">Sítio</option>
                <option value="retiro">Retiro</option>
                <option value="outro">Outro</option>
              </select>
            </label>
          </div>
          <div style={sRow}>
            <label style={sLabel}>
              Município
              <input style={sInput} value={form.municipio} onChange={campo("municipio")} />
            </label>
            <label style={sLabel}>
              UF (2 letras)
              <input style={sInput} value={form.uf} onChange={campo("uf")} maxLength={2} />
            </label>
            <label style={sLabel}>
              Bioma
              <input style={sInput} value={form.bioma} onChange={campo("bioma")} placeholder="ex: Cerrado" />
            </label>
          </div>
          <div style={sRow}>
            <label style={sLabel}>
              Latitude
              <input style={sInput} type="number" step="any" value={form.latitude} onChange={campo("latitude")} />
            </label>
            <label style={sLabel}>
              Longitude
              <input style={sInput} type="number" step="any" value={form.longitude} onChange={campo("longitude")} />
            </label>
            <label style={sLabel}>
              Área (ha)
              <input style={sInput} type="number" step="any" min="0" value={form.area_hectares} onChange={campo("area_hectares")} />
            </label>
          </div>
          <div style={sRow}>
            <label style={sLabel}>
              Código SISBOV
              <input style={sInput} value={form.codigo_sisbov} onChange={campo("codigo_sisbov")} />
            </label>
            <label style={sLabel}>
              Inscrição Estadual
              <input style={sInput} value={form.inscricao_estadual} onChange={campo("inscricao_estadual")} />
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

// ---- Seção de Lote ----
function SecaoLote() {
  const [aberta, setAberta] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [ok, setOk] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [fazendas, setFazendas] = useState<Fazenda[]>([]);

  const inicial = { fazenda_id: "", nome: "", categoria: "garrote" as Lote["categoria"] };
  const [form, setForm] = useState(inicial);

  useEffect(() => {
    get<Fazenda[]>("/fazendas").then(setFazendas).catch(() => {});
  }, []);

  function campo(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setOk(null); setErro(null); setEnviando(true);
    try {
      await post("/lotes", { fazenda_id: form.fazenda_id, nome: form.nome, categoria: form.categoria });
      setOk("Lote criado com sucesso!");
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
        <span>{aberta ? "▼" : "▶"}</span> Novo Lote
      </div>
      {aberta && (
        <form onSubmit={salvar} style={sForm}>
          <div style={sRow}>
            <label style={sLabel}>
              Fazenda <span style={{ color: "#dc2626" }}>*</span>
              <select required style={sInput} value={form.fazenda_id} onChange={campo("fazenda_id")}>
                <option value="">(selecione)</option>
                {fazendas.map((f) => (
                  <option key={f.id} value={f.id}>{f.nome}</option>
                ))}
              </select>
            </label>
            <label style={sLabel}>
              Nome <span style={{ color: "#dc2626" }}>*</span>
              <input required style={sInput} value={form.nome} onChange={campo("nome")} />
            </label>
            <label style={sLabel}>
              Categoria <span style={{ color: "#dc2626" }}>*</span>
              <select required style={sInput} value={form.categoria} onChange={campo("categoria")}>
                <option value="bezerro">Bezerro</option>
                <option value="garrote">Garrote</option>
                <option value="novilha">Novilha</option>
                <option value="matriz">Matriz</option>
                <option value="touro">Touro</option>
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

// ---- Seção de Animal ----
function SecaoAnimal() {
  const [aberta, setAberta] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [ok, setOk] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [fazendas, setFazendas] = useState<Fazenda[]>([]);
  const [lotes, setLotes] = useState<Lote[]>([]);

  const inicial = {
    fazenda_id: "", lote_id: "", brinco: "", rgn: "", rgd: "", ceip: false,
    rfid: "", raca: "Nelore", variedade: "" as "" | "padrao" | "mocho",
    sexo: "" as "" | "M" | "F", nascimento: "", situacao: "ativo",
    data_entrada: "", observacoes: "",
  };
  const [form, setForm] = useState(inicial);

  useEffect(() => {
    get<Fazenda[]>("/fazendas").then(setFazendas).catch(() => {});
  }, []);

  useEffect(() => {
    if (!form.fazenda_id) { setLotes([]); return; }
    get<Lote[]>(`/lotes?fazenda_id=${form.fazenda_id}`).then(setLotes).catch(() => {});
  }, [form.fazenda_id]);

  function campo(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setOk(null); setErro(null); setEnviando(true);
    try {
      const body: Record<string, unknown> = {
        fazenda_id: form.fazenda_id,
        sexo: form.sexo,
        raca: form.raca || "Nelore",
        situacao: form.situacao || "ativo",
        ceip: form.ceip,
      };
      if (form.lote_id) body.lote_id = form.lote_id;
      if (form.brinco) body.brinco = form.brinco;
      if (form.rgn) body.rgn = form.rgn;
      if (form.rgd) body.rgd = form.rgd;
      if (form.rfid) body.rfid = form.rfid;
      if (form.variedade) body.variedade = form.variedade;
      if (form.nascimento) body.nascimento = form.nascimento;
      if (form.data_entrada) body.data_entrada = form.data_entrada;
      if (form.observacoes) body.observacoes = form.observacoes;
      await post("/animais", body);
      setOk("Animal cadastrado com sucesso!");
      setForm(inicial);
      setLotes([]);
    } catch (err) {
      setErro(String(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={sCard}>
      <div style={sHeader} onClick={() => setAberta((v) => !v)}>
        <span>{aberta ? "▼" : "▶"}</span> Novo Animal
      </div>
      {aberta && (
        <form onSubmit={salvar} style={sForm}>
          <div style={sRow}>
            <label style={sLabel}>
              Fazenda <span style={{ color: "#dc2626" }}>*</span>
              <select
                required
                style={sInput}
                value={form.fazenda_id}
                onChange={(e) => setForm((f) => ({ ...f, fazenda_id: e.target.value, lote_id: "" }))}
              >
                <option value="">(selecione)</option>
                {fazendas.map((f) => (
                  <option key={f.id} value={f.id}>{f.nome}</option>
                ))}
              </select>
            </label>
            <label style={sLabel}>
              Lote
              <select
                style={sInput}
                value={form.lote_id}
                onChange={campo("lote_id")}
                disabled={!form.fazenda_id}
              >
                <option value="">(sem lote)</option>
                {lotes.map((l) => (
                  <option key={l.id} value={l.id}>{l.nome} — {l.categoria}</option>
                ))}
              </select>
            </label>
          </div>
          <div style={sRow}>
            <label style={sLabel}>
              Sexo <span style={{ color: "#dc2626" }}>*</span>
              <select required style={sInput} value={form.sexo} onChange={campo("sexo")}>
                <option value="">(selecione)</option>
                <option value="M">Macho</option>
                <option value="F">Fêmea</option>
              </select>
            </label>
            <label style={sLabel}>
              Brinco
              <input style={sInput} value={form.brinco} onChange={campo("brinco")} />
            </label>
            <label style={sLabel}>
              RGN
              <input style={sInput} value={form.rgn} onChange={campo("rgn")} />
            </label>
            <label style={sLabel}>
              RGD
              <input style={sInput} value={form.rgd} onChange={campo("rgd")} />
            </label>
          </div>
          <div style={sRow}>
            <label style={sLabel}>
              Raça
              <input style={sInput} value={form.raca} onChange={campo("raca")} />
            </label>
            <label style={sLabel}>
              Variedade
              <select style={sInput} value={form.variedade} onChange={campo("variedade")}>
                <option value="">(não informado)</option>
                <option value="padrao">Padrão</option>
                <option value="mocho">Mocho</option>
              </select>
            </label>
            <label style={sLabel}>
              RFID
              <input style={sInput} value={form.rfid} onChange={campo("rfid")} />
            </label>
          </div>
          <div style={sRow}>
            <label style={sLabel}>
              Data de nascimento
              <input style={sInput} type="date" value={form.nascimento} onChange={campo("nascimento")} />
            </label>
            <label style={sLabel}>
              Data de entrada
              <input style={sInput} type="date" value={form.data_entrada} onChange={campo("data_entrada")} />
            </label>
            <label style={sLabel}>
              Situação
              <select style={sInput} value={form.situacao} onChange={campo("situacao")}>
                <option value="ativo">Ativo</option>
                <option value="vendido">Vendido</option>
                <option value="morto">Morto</option>
                <option value="descartado">Descartado</option>
              </select>
            </label>
          </div>
          <label style={sLabel}>
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={form.ceip}
                onChange={(e) => setForm((f) => ({ ...f, ceip: e.target.checked }))}
              />
              CEIP (Certificado Especial de Identificação e Produção)
            </span>
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
export function Cadastros() {
  return (
    <section style={{ maxWidth: 860, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif", color: "#111827" }}>
      <h2 style={{ margin: "0 0 20px" }}>Cadastros</h2>
      <SecaoFazenda />
      <SecaoLote />
      <SecaoAnimal />
    </section>
  );
}
