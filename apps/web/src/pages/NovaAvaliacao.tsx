import { useEffect, useState } from "react";
import {
  post,
  uploadArquivo,
  type Animal,
  type Fazenda,
  type FrameExtraidoResponse,
} from "../api/client";
import { cacheAnimal, cacheAnimais, cacheFazendas, postarComOutbox } from "../offline/sync";
import { CameraCaptura } from "../camera/CameraCaptura";
import { KeypointsCanvas } from "../components/KeypointsCanvas";
import { pontosIniciaisPadrao } from "../keypoint-utils";
import type { Keypoint } from "../types";

const LARGURA = 1280;
const ALTURA = 720;

type FonteImagem = "camera" | "video" | "imagem";

interface Props {
  animalIdInicial?: string;
  onConcluido: (animalId: string) => void;
  onCancelar: () => void;
}

export function NovaAvaliacao({ animalIdInicial, onConcluido, onCancelar }: Props) {
  const [fazendas, setFazendas] = useState<Fazenda[]>([]);
  const [fazendaId, setFazendaId] = useState("");
  const [animais, setAnimais] = useState<Animal[]>([]);
  const [animalId, setAnimalId] = useState(animalIdInicial ?? "");
  const [animal, setAnimal] = useState<Animal | null>(null);

  const [pontos, setPontos] = useState<Keypoint[]>(() => pontosIniciaisPadrao(LARGURA, ALTURA));
  const [frameUrl, setFrameUrl] = useState<string | undefined>(undefined);
  const [pxPorCm, setPxPorCm] = useState("5");
  const [larguraGarupa, setLarguraGarupa] = useState("");
  const [idadeMesesOverride, setIdadeMesesOverride] = useState("");

  const [fonteImagem, setFonteImagem] = useState<FonteImagem>("imagem");
  const [carregandoVideo, setCarregandoVideo] = useState(false);

  // Escore do tecnico (ECC + EPMURAS)
  const [mostrarEscore, setMostrarEscore] = useState(false);
  const [ecc, setEcc] = useState("");
  const [epmE, setEpmE] = useState("");
  const [epmP, setEpmP] = useState("");
  const [epmM, setEpmM] = useState("");
  const [epmU, setEpmU] = useState("");
  const [epmR, setEpmR] = useState("");
  const [epmA, setEpmA] = useState("");
  const [epmS, setEpmS] = useState("");

  // Medidas manuais de referencia (subconjunto ~1:3)
  const [mostrarManuais, setMostrarManuais] = useState(false);
  const [manCernelha, setManCernelha] = useState("");
  const [manGarupa, setManGarupa] = useState("");
  const [manComprimento, setManComprimento] = useState("");
  const [manLarguraGarupa, setManLarguraGarupa] = useState("");
  const [manPerimetro, setManPerimetro] = useState("");

  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [enfileirado, setEnfileirado] = useState(false);

  useEffect(() => {
    cacheFazendas().then(setFazendas).catch(() => {});
  }, []);

  useEffect(() => {
    if (!fazendaId) return;
    cacheAnimais(fazendaId).then(setAnimais).catch(() => {});
  }, [fazendaId]);

  useEffect(() => {
    if (!animalId) { setAnimal(null); return; }
    cacheAnimal(animalId).then((a) => setAnimal(a ?? null)).catch(() => {});
  }, [animalId]);

  function escolherImagemLocal(ev: React.ChangeEvent<HTMLInputElement>) {
    const file = ev.target.files?.[0];
    if (!file) return;
    if (frameUrl) URL.revokeObjectURL(frameUrl);
    setFrameUrl(URL.createObjectURL(file));
  }

  async function processarVideo(ev: React.ChangeEvent<HTMLInputElement>) {
    const file = ev.target.files?.[0];
    if (!file) return;
    setCarregandoVideo(true);
    setErro(null);
    setFrameUrl(undefined);
    try {
      const resp = await uploadArquivo<FrameExtraidoResponse>(
        "/capturas/extrair-frame",
        file,
      );
      setFrameUrl(resp.frame_url);
    } catch (e) {
      setErro(`Falha ao processar vídeo: ${String(e)}`);
    } finally {
      setCarregandoVideo(false);
    }
  }

  function calcularIdadeMeses(): number | null {
    if (idadeMesesOverride) return parseFloat(idadeMesesOverride);
    if (!animal?.nascimento) return null;
    const nasc = new Date(animal.nascimento);
    const hoje = new Date();
    const meses = (hoje.getFullYear() - nasc.getFullYear()) * 12 +
      (hoje.getMonth() - nasc.getMonth());
    return Math.max(1, meses);
  }

  async function enviar() {
    if (!animalId || !animal) { setErro("Selecione o animal."); return; }
    const scale = parseFloat(pxPorCm);
    if (!scale || scale <= 0) { setErro("px/cm inválido."); return; }
    const idadeMeses = calcularIdadeMeses();
    if (!idadeMeses || idadeMeses <= 0) {
      setErro("Informe a idade em meses ou cadastre a data de nascimento do animal."); return;
    }

    const sexo = animal.sexo === "M" ? "macho" : "femea";
    const keypointsCm = pontos.map((p) => ({
      id: p.id,
      x: p.x / scale,
      y: p.y / scale,
    }));

    const hasEcc = !!ecc;
    const hasEpmuras = !!(epmE || epmP || epmM || epmU || epmR || epmA || epmS);
    const escorePayload = (hasEcc || hasEpmuras) ? {
      ecc: ecc ? parseFloat(ecc) : undefined,
      e: epmE ? parseInt(epmE, 10) : undefined,
      p: epmP ? parseInt(epmP, 10) : undefined,
      m: epmM ? parseInt(epmM, 10) : undefined,
      u: epmU ? parseInt(epmU, 10) : undefined,
      r: epmR ? parseInt(epmR, 10) : undefined,
      a: epmA ? parseInt(epmA, 10) : undefined,
      s: epmS ? parseInt(epmS, 10) : undefined,
    } : undefined;

    const anyManual = !!(manCernelha || manGarupa || manComprimento || manLarguraGarupa || manPerimetro);
    const medidasManuaisPayload = anyManual ? {
      altura_cernelha_cm: manCernelha ? parseFloat(manCernelha) : undefined,
      altura_garupa_cm: manGarupa ? parseFloat(manGarupa) : undefined,
      comprimento_corporal_cm: manComprimento ? parseFloat(manComprimento) : undefined,
      largura_garupa_cm: manLarguraGarupa ? parseFloat(manLarguraGarupa) : undefined,
      perimetro_toracico_cm: manPerimetro ? parseFloat(manPerimetro) : undefined,
    } : undefined;

    const payload = {
      animal_id: animalId,
      data_hora: new Date().toISOString(),
      sexo,
      idade_meses: idadeMeses,
      keypoints_cm: keypointsCm,
      largura_garupa_cm: larguraGarupa ? parseFloat(larguraGarupa) : undefined,
      px_por_cm: parseFloat(pxPorCm) || undefined,
      escore: escorePayload,
      medidas_manuais: medidasManuaisPayload,
    };

    setEnviando(true);
    setErro(null);
    setEnfileirado(false);
    try {
      const { resultado, enfileirado: eq } = await postarComOutbox("/avaliacoes", payload);
      if (eq) {
        setEnfileirado(true);
      } else {
        // salva frame como captura permanente (silencioso — não bloqueia o fluxo)
        if (frameUrl?.startsWith("http") && resultado) {
          const av = resultado as { id: string };
          post<unknown>("/capturas", {
            avaliacao_id: av.id,
            arquivo_url: frameUrl,
            tipo: "foto",
            vista: "lateral",
          }).catch(() => {});
        }
        onConcluido(animalId);
      }
    } catch (e) {
      setErro(String(e));
    } finally {
      setEnviando(false);
    }
  }

  const tabStyle = (aba: FonteImagem): React.CSSProperties => ({
    padding: "6px 16px",
    fontSize: 13,
    border: "none",
    borderBottom: fonteImagem === aba ? "2px solid #059669" : "2px solid transparent",
    background: "none",
    color: fonteImagem === aba ? "#059669" : "#6b7280",
    fontWeight: fonteImagem === aba ? 600 : 400,
    cursor: "pointer",
  });

  return (
    <section style={{ maxWidth: 1024, margin: "0 auto", padding: 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <h2 style={{ margin: 0 }}>Nova avaliação</h2>
        <button type="button" onClick={onCancelar} style={{ marginLeft: "auto" }}>
          Cancelar
        </button>
      </div>

      {/* Seleção do animal */}
      {!animalIdInicial && (
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16, padding: 12, background: "#f9fafb", borderRadius: 8 }}>
          <label>
            Fazenda:{" "}
            <select value={fazendaId} onChange={(e) => { setFazendaId(e.target.value); setAnimalId(""); }}>
              <option value="">(selecione)</option>
              {fazendas.map((f) => <option key={f.id} value={f.id}>{f.nome}</option>)}
            </select>
          </label>
          <label>
            Animal:{" "}
            <select value={animalId} onChange={(e) => setAnimalId(e.target.value)} disabled={!fazendaId}>
              <option value="">(selecione)</option>
              {animais.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.brinco ?? "(sem brinco)"} · {a.sexo}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      {animal && (
        <div style={{ marginBottom: 12, fontSize: 13, color: "#374151" }}>
          Animal: <strong>{animal.brinco ?? "(sem brinco)"}</strong> · {animal.sexo} ·{" "}
          {calcularIdadeMeses() ? `${calcularIdadeMeses()!.toFixed(1)} meses` : "idade desconhecida"}
        </div>
      )}

      {/* Parâmetros de calibração */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 16, padding: 12, background: "#f9fafb", borderRadius: 8 }}>
        <label style={{ fontSize: 13 }}>
          Escala px/cm:{" "}
          <input
            type="number" min="0.1" step="0.1" value={pxPorCm}
            onChange={(e) => setPxPorCm(e.target.value)} style={{ width: 70 }}
          />
          <span style={{ marginLeft: 6, color: "#6b7280" }}>(placa 40 cm → px÷40)</span>
        </label>
        <label style={{ fontSize: 13 }}>
          Largura garupa (cm):{" "}
          <input
            type="number" min="0" step="0.5" value={larguraGarupa}
            onChange={(e) => setLarguraGarupa(e.target.value)}
            placeholder="opcional" style={{ width: 70 }}
          />
        </label>
        {!animal?.nascimento && (
          <label style={{ fontSize: 13 }}>
            Idade (meses):{" "}
            <input
              type="number" min="1" step="1" value={idadeMesesOverride}
              onChange={(e) => setIdadeMesesOverride(e.target.value)}
              placeholder="obrigatório" style={{ width: 80 }}
            />
          </label>
        )}
      </div>

      {/* Abas de fonte de imagem */}
      <div style={{ borderBottom: "1px solid #e5e7eb", marginBottom: 12 }}>
        <button type="button" style={tabStyle("camera")} onClick={() => setFonteImagem("camera")}>
          Câmera
        </button>
        <button type="button" style={tabStyle("video")} onClick={() => setFonteImagem("video")}>
          Vídeo
        </button>
        <button type="button" style={tabStyle("imagem")} onClick={() => setFonteImagem("imagem")}>
          Imagem
        </button>
      </div>

      {/* Conteúdo da aba */}
      <div style={{ marginBottom: 12 }}>
        {fonteImagem === "camera" && (
          <CameraCaptura onCaptura={(url) => setFrameUrl(url)} />
        )}

        {fonteImagem === "video" && (
          <div>
            <label style={{ fontSize: 13, color: "#374151" }}>
              Selecione um vídeo (mp4, mov, avi):{" "}
              <input
                type="file"
                accept="video/*"
                onChange={processarVideo}
                aria-label="Carregar vídeo"
              />
            </label>
            {carregandoVideo && (
              <div style={{ marginTop: 8, fontSize: 13, color: "#6b7280" }}>
                Extraindo melhor frame… (pode levar alguns segundos)
              </div>
            )}
            {frameUrl && fonteImagem === "video" && (
              <div style={{ marginTop: 8, fontSize: 13, color: "#059669" }}>
                Frame extraído com sucesso.
              </div>
            )}
          </div>
        )}

        {fonteImagem === "imagem" && (
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <input type="file" accept="image/*" onChange={escolherImagemLocal} aria-label="Carregar frame" />
          </div>
        )}
      </div>

      {/* Canvas de keypoints */}
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <button type="button" onClick={() => setPontos(pontosIniciaisPadrao(LARGURA, ALTURA))}>
          Reiniciar pontos
        </button>
        <span style={{ marginLeft: "auto", fontSize: 13, color: "#374151" }}>
          Corrigidos: <strong>{pontos.filter((p) => p.corrigido).length}</strong> / {pontos.length}
        </span>
      </div>

      <KeypointsCanvas
        pontos={pontos}
        largura={LARGURA}
        altura={ALTURA}
        onChange={setPontos}
        frameUrl={frameUrl}
      />

      {/* Secao A: Notas do tecnico (ECC e EPMURAS) */}
      <div style={{ marginTop: 16, border: "1px solid #e5e7eb", borderRadius: 8 }}>
        <button
          type="button"
          onClick={() => setMostrarEscore((v) => !v)}
          style={{
            width: "100%", textAlign: "left", padding: "10px 14px",
            background: "#f9fafb", border: "none", borderRadius: 8,
            cursor: "pointer", fontWeight: 600, fontSize: 13, color: "#374151",
          }}
        >
          {mostrarEscore ? "▲" : "▼"} Notas do técnico (ECC e EPMURAS) — opcional
        </button>
        {mostrarEscore && (
          <div style={{ padding: 14, display: "flex", gap: 12, flexWrap: "wrap" }}>
            <label style={{ fontSize: 13 }}>
              ECC (1–9):{" "}
              <input
                type="number" min="1" max="9" step="0.5" value={ecc}
                onChange={(e) => setEcc(e.target.value)} style={{ width: 60 }}
                placeholder="ex: 3.5"
              />
            </label>
            {[
              ["E (Estrutura)", epmE, setEpmE],
              ["P (Precocidade)", epmP, setEpmP],
              ["M (Musculosidade)", epmM, setEpmM],
              ["U (Umbigo)", epmU, setEpmU],
              ["R (Racial)", epmR, setEpmR],
              ["A (Aprumos)", epmA, setEpmA],
              ["S (Sexualidade)", epmS, setEpmS],
            ].map(([label, val, setter]) => (
              <label key={String(label)} style={{ fontSize: 13 }}>
                {String(label)}:{" "}
                <input
                  type="number" min="1" max="6" step="1"
                  value={String(val)}
                  onChange={(e) => (setter as React.Dispatch<React.SetStateAction<string>>)(e.target.value)}
                  style={{ width: 50 }}
                />
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Secao B: Medidas manuais de referencia (~1:3) */}
      <div style={{ marginTop: 10, border: "1px solid #e5e7eb", borderRadius: 8 }}>
        <button
          type="button"
          onClick={() => setMostrarManuais((v) => !v)}
          style={{
            width: "100%", textAlign: "left", padding: "10px 14px",
            background: "#f9fafb", border: "none", borderRadius: 8,
            cursor: "pointer", fontWeight: 600, fontSize: 13, color: "#374151",
          }}
        >
          {mostrarManuais ? "▲" : "▼"} Medidas manuais de referência (~1:3) — opcional
        </button>
        {mostrarManuais && (
          <div style={{ padding: 14, display: "flex", gap: 12, flexWrap: "wrap" }}>
            {[
              ["Altura cernelha (cm)", manCernelha, setManCernelha],
              ["Altura garupa (cm)", manGarupa, setManGarupa],
              ["Comprimento corporal (cm)", manComprimento, setManComprimento],
              ["Largura garupa (cm)", manLarguraGarupa, setManLarguraGarupa],
              ["Perímetro torácico (cm)", manPerimetro, setManPerimetro],
            ].map(([label, val, setter]) => (
              <label key={String(label)} style={{ fontSize: 13 }}>
                {String(label)}:{" "}
                <input
                  type="number" min="0" step="0.5"
                  value={String(val)}
                  onChange={(e) => (setter as React.Dispatch<React.SetStateAction<string>>)(e.target.value)}
                  style={{ width: 70 }}
                  placeholder="cm"
                />
              </label>
            ))}
          </div>
        )}
      </div>

      {erro && (
        <div style={{ marginTop: 12, padding: 10, background: "#fee2e2", color: "#991b1b", borderRadius: 6 }}>
          {erro}
        </div>
      )}

      {enfileirado && (
        <div style={{ marginTop: 12, padding: 10, background: "#dbeafe", color: "#1d4ed8", borderRadius: 6 }}>
          Avaliação salva para sincronizar quando a conexão for restaurada.
        </div>
      )}

      <button
        type="button"
        onClick={enviar}
        disabled={enviando || !animalId}
        style={{
          marginTop: 16,
          padding: "10px 28px",
          background: enviando ? "#d1fae5" : "#059669",
          color: "white",
          border: "none",
          borderRadius: 6,
          fontSize: 15,
          fontWeight: 600,
          cursor: enviando ? "default" : "pointer",
        }}
      >
        {enviando ? "Enviando…" : "Enviar avaliação"}
      </button>
    </section>
  );
}
