import { useEffect, useRef, useState } from "react";

interface Props {
  onCaptura: (blobUrl: string) => void;
}

// Silhueta simplificada de bovino Nelore (perfil lateral, normalizada 0-100)
const SILHUETA_D = [
  "M 5,55 Q 10,30 20,25 Q 30,20 40,18",    // focinho → cernelha
  "Q 55,15 60,13 Q 65,10 70,14",            // cernelha → cupim
  "Q 80,18 90,20 Q 100,22 110,25",          // cernelha → anca
  "Q 120,28 130,32 Q 138,40 140,50",        // anca → garupa
  "Q 142,58 140,65 L 135,90 L 130,98",      // cauda → membro posterior
  "L 115,98 L 112,65 Q 108,55 100,52",      // volta membro posterior
  "Q 90,50 80,52 Q 70,55 68,65",            // ventre → membro anterior
  "L 65,98 L 50,98 L 48,65",               // membro anterior
  "Q 44,52 38,48 Q 30,45 25,48",            // linha ventral
  "Q 15,52 8,58 Z",                          // fecha
].join(" ");

export function CameraCaptura({ onCaptura }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [ativo, setAtivo] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [capturado, setCapturado] = useState(false);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  async function iniciarCamera() {
    setErro(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setAtivo(true);
      setCapturado(false);
    } catch (e) {
      setErro(`Câmera indisponível: ${(e as Error).message}`);
    }
  }

  function pararCamera() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setAtivo(false);
  }

  function capturar() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        setCapturado(true);
        pararCamera();
        onCaptura(url);
      },
      "image/jpeg",
      0.92,
    );
  }

  const W = 640;
  const H = 360;

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      {!ativo && !capturado && (
        <button
          type="button"
          onClick={iniciarCamera}
          style={{
            padding: "10px 20px",
            background: "#1d4ed8",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            fontSize: 14,
            cursor: "pointer",
          }}
        >
          Abrir câmera
        </button>
      )}

      {ativo && (
        <div style={{ position: "relative" }}>
          <video
            ref={videoRef}
            width={W}
            height={H}
            style={{ display: "block", borderRadius: 6, background: "#000" }}
            muted
            playsInline
          />
          {/* Guia de silhueta */}
          <svg
            width={W}
            height={H}
            viewBox="0 0 150 110"
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              pointerEvents: "none",
              opacity: 0.45,
            }}
          >
            <path d={SILHUETA_D} fill="none" stroke="#22c55e" strokeWidth="1.5" />
          </svg>
          <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
            <button
              type="button"
              onClick={capturar}
              style={{
                flex: 1,
                padding: "10px 0",
                background: "#059669",
                color: "#fff",
                border: "none",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Capturar foto
            </button>
            <button
              type="button"
              onClick={pararCamera}
              style={{
                padding: "10px 16px",
                background: "#6b7280",
                color: "#fff",
                border: "none",
                borderRadius: 6,
                fontSize: 14,
                cursor: "pointer",
              }}
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {capturado && (
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ color: "#059669", fontSize: 13 }}>Foto capturada.</span>
          <button
            type="button"
            onClick={() => { setCapturado(false); iniciarCamera(); }}
            style={{ fontSize: 12, color: "#6b7280", background: "none", border: "none", cursor: "pointer" }}
          >
            Tirar nova
          </button>
        </div>
      )}

      {erro && (
        <div style={{ marginTop: 8, color: "#dc2626", fontSize: 13 }}>{erro}</div>
      )}

      {/* canvas oculto para captura */}
      <canvas ref={canvasRef} style={{ display: "none" }} />
    </div>
  );
}
