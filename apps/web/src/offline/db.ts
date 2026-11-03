/**
 * Banco local IndexedDB via Dexie.
 *
 * Tabelas:
 *   fazendas  — cache de GET /fazendas
 *   animais   — cache de GET /animais?fazenda_id=...
 *   outbox    — avaliações criadas offline aguardando sincronização
 */
import Dexie, { type EntityTable } from "dexie";

import type { Animal, Fazenda } from "../api/client";

export interface OutboxItem {
  id?: number;          // auto-increment
  local_id: string;     // UUID gerado no cliente (para deduplicação futura)
  path: string;         // ex: "/avaliacoes"
  payload: unknown;
  criado_em: string;    // ISO-8601
  tentativas: number;
}

class IndexBeefDB extends Dexie {
  fazendas!: EntityTable<Fazenda, "id">;
  animais!: EntityTable<Animal, "id">;
  outbox!: EntityTable<OutboxItem, "id">;

  constructor() {
    super("indexbeef");
    this.version(1).stores({
      fazendas: "id",
      animais: "id, fazenda_id",
      outbox: "++id, tentativas",
    });
  }
}

export const db = new IndexBeefDB();
