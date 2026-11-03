import { useEffect, useState } from "react";
import { contarPendentes, sincronizarOutbox } from "./sync";

export function StatusOffline() {
  const [online, setOnline] = useState(navigator.onLine);
  const [pendentes, setPendentes] = useState(0);
  const [sincronizando, setSincronizando] = useState(false);

  useEffect(() => {
    const atualizar = () => setOnline(navigator.onLine);
    window.addEventListener("online", atualizar);
    window.addEventListener("offline", atualizar);
    return () => {
      window.removeEventListener("online", atualizar);
      window.removeEventListener("offline", atualizar);
    };
  }, []);

  // Atualiza a contagem de pendentes a cada 5 s
  useEffect(() => {
    let ativo = true;
    const poll = async () => {
      if (!ativo) return;
      setPendentes(await contarPendentes());
    };
    void poll();
    const id = setInterval(() => void poll(), 5_000);
    return () => {
      ativo = false;
      clearInterval(id);
    };
  }, []);

  // Sincroniza automaticamente ao voltar online
  useEffect(() => {
    if (!online) return;
    const sync = async () => {
      const n = await contarPendentes();
      if (n === 0) return;
      setSincronizando(true);
      try {
        await sincronizarOutbox();
        setPendentes(await contarPendentes());
      } finally {
        setSincronizando(false);
      }
    };
    void sync();
  }, [online]);

  if (online && pendentes === 0 && !sincronizando) return null;

  const cor = online ? "#1d4ed8" : "#dc2626";
  const texto = sincronizando
    ? "↑ Sincronizando…"
    : online
      ? `↑ ${pendentes} avaliação${pendentes !== 1 ? "ões" : ""} para sincronizar`
      : `● Offline${pendentes > 0 ? ` · ${pendentes} pendente${pendentes !== 1 ? "s" : ""}` : ""}`;

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: "fixed",
        bottom: 16,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 9_999,
        background: cor,
        color: "#fff",
        padding: "6px 16px",
        borderRadius: 20,
        fontSize: 13,
        fontWeight: 500,
        boxShadow: "0 2px 8px rgba(0,0,0,.25)",
        whiteSpace: "nowrap",
      }}
    >
      {texto}
    </div>
  );
}
