// Cliente HTTP minimalista para o backend (fetch nativo, sem axios).

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

export function post<T>(path: string, body: unknown): Promise<T> {
  return _request<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export async function getBlob(path: string): Promise<Blob> {
  const r = await fetch(`${API_URL}${path}`);
  if (!r.ok) {
    const texto = await r.text();
    throw new Error(`${r.status} ${r.statusText}: ${texto}`);
  }
  return r.blob();
}

// --- Tipos de domínio ---

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

export interface MedidasAvaliacao {
  altura_cernelha_cm?: number | null;
  altura_cernelha_conf?: number | null;
  altura_garupa_cm?: number | null;
  comprimento_corporal_cm?: number | null;
  comprimento_corporal_conf?: number | null;
  profundidade_toracica_cm?: number | null;
  comprimento_garupa_cm?: number | null;
  largura_garupa_cm?: number | null;
  altura_cupim_cm?: number | null;
  umbigo_chao_cm?: number | null;
  perimetro_toracico_est_cm?: number | null;
  inclinacao_garupa_graus?: number | null;
  jarrete_graus?: number | null;
}

export interface CaixaVirtualAvaliacao {
  c_cm?: number | null;
  p_cm?: number | null;
  l_cm?: number | null;
  volume_l?: number | null;
  ipl?: number | null;
  compacidade?: number | null;
  indice_comprimento?: number | null;
}

export interface PredicaoAvaliacao {
  tipo: string;
  valor?: number | null;
  faixa_min?: number | null;
  faixa_max?: number | null;
  metodo?: string | null;
}

export interface Avaliacao {
  id: string;
  animal_id: string;
  data_hora: string;
  status: "capturada" | "processando" | "revisar" | "concluida" | "erro";
  versao_pipeline?: string | null;
  observacoes?: string | null;
  resultado?: Record<string, unknown> | null;
  medida?: MedidasAvaliacao | null;
  caixa_virtual?: CaixaVirtualAvaliacao | null;
  predicoes?: PredicaoAvaliacao[];
}

export interface AvaliacaoListItem {
  id: string;
  data_hora: string;
  status: Avaliacao["status"];
  versao_pipeline?: string | null;
  observacoes?: string | null;
}

export interface DashboardAlertaBateria {
  dispositivo_id: string;
  dispositivo_modelo?: string | null;
  animal_id?: string | null;
  animal_brinco?: string | null;
  bateria_pct: number;
  timestamp: string;
}

export interface DashboardAnimalFora {
  animal_id: string;
  animal_brinco?: string | null;
  geofence_id: string;
  geofence_nome?: string | null;
  saida_em: string;
}

export interface DashboardGeofence {
  id: string;
  nome: string;
  tipo: string;
  poligono_wkt: string;
}

export interface Dashboard {
  fazenda_id: string;
  fazenda_nome: string;
  total_animais: number;
  animais_por_sexo: Record<string, number>;
  campanhas_ativas: number;
  pesagens_recentes_7d: number;
  avaliacoes_semana: number;
  alertas_bateria: DashboardAlertaBateria[];
  animais_fora_cerca: DashboardAnimalFora[];
  geofences: DashboardGeofence[];
}
