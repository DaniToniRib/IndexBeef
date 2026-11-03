/**
 * Web Worker para inferência de keypoints no browser via ONNX Runtime Web.
 *
 * Ativado quando o modelo ONNX estiver disponível em /modelos/keypoints.onnx.
 *
 * Mensagens recebidas:
 *   { type: "load";  modelUrl: string }
 *   { type: "infer"; imageData: ImageData }
 *
 * Mensagens enviadas:
 *   { type: "loaded" }
 *   { type: "result"; keypoints: null | unknown[] }
 *   { type: "error";  message: string }
 */

let session: unknown = null;

self.onmessage = async (e: MessageEvent) => {
  const msg = e.data as { type: string };

  if (msg.type === "load") {
    const { modelUrl } = e.data as { type: "load"; modelUrl: string };
    try {
      // onnxruntime-web e carregado dinamicamente para nao bloquear o bundle principal
      // @ts-expect-error onnxruntime-web carregado dinamicamente
      const ort = (await import("onnxruntime-web")) as {
        InferenceSession: { create(url: string): Promise<unknown> };
      };
      session = await ort.InferenceSession.create(modelUrl);
      self.postMessage({ type: "loaded" });
    } catch (err) {
      self.postMessage({ type: "error", message: String(err) });
    }
  } else if (msg.type === "infer") {
    if (!session) {
      self.postMessage({ type: "result", keypoints: null });
      return;
    }
    // Processamento real depende do modelo treinado exportado para ONNX.
    // O pipeline completo sera implementado em Fase 6 apos o dataset do Pantanal
    // estar disponivel (Fase 2) e o modelo treinado (Fase 3).
    // Por ora retorna null para indicar que a inferencia no browser esta desativada.
    self.postMessage({ type: "result", keypoints: null });
  }
};
