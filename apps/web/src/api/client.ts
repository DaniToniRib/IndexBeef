// Cliente HTTP minimalista para o backend (fetch nativo, sem axios).
// O base URL vem da env de Vite (VITE_API_URL) com fallback para localhost:8000.

export const API_URL: string =
  (import.meta.env?.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

async function _request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!r.ok) {
    const texto = await r.text();
    throw new Error(`${r.status} ${r.statusText}: ${texto}`);
  }
  return (await r.json()) as T;
}

export const get = <T>(path: string) => _request<T>(path);

export interface Fazenda {
  id: string;
  nome: string;
  tipo: "fazenda" | "sitio" | "retiro" | "outro";
  municipio?: string | null;
  uf?: string | null;
  bioma?: string | null;
}

export interface Animal {
  id: string;
  fazenda_id: string;
  lote_id?: string | null;
  brinco?: string | null;
  rgn?: string | null;
  ceip: boolean;
  sexo: "M" | "F";
  nascimento?: string | null;
  situacao: string;
  raca: string;
  data_entrada?: string | null;
  observacoes?: string | null;
}

export interface PesagemHistorico {
  id: string;
  data: string;
  peso_kg: string;
  origem: string;
  gmd_kg_dia: number | null;
}

export interface AnimalHistorico {
  animal_id: string;
  pesagens: PesagemHistorico[];
  gmd_total_kg_dia: number | null;
  peso_atual_kg: string | null;
  idade_dias: number | null;
  idade_meses: number | null;
}

export interface AplicacaoSanitaria {
  id: string;
  tipo: "vacina" | "vermifugo" | "terapeutico";
  data: string;
  principio_ativo: string;
  nome_comercial?: string | null;
  via: string;
  carencia_abate_dias?: number | null;
  veterinario_crmv?: string | null;
  apto_abate_em?: string | null;
}

export interface AtendimentoVeterinario {
  id: string;
  data_hora: string;
  veterinario_nome: string;
  veterinario_crmv: string;
  motivo: string;
  diagnostico?: string | null;
}

export interface EventoGeofence {
  id: string;
  geofence_id: string;
  tipo: "entrada" | "saida";
  timestamp: string;
}
