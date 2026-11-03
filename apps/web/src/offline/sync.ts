/**
 * Funções de cache e outbox para suporte offline.
 *
 * Uso:
 *   - cacheFazendas() / cacheAnimais(): substituem get() com fallback IndexedDB
 *   - postarComOutbox(): substitui post() para /avaliacoes; guarda localmente se offline
 *   - sincronizarOutbox(): dispara ao voltar online
 */
import { get, post } from "../api/client";
import type { Animal, Fazenda } from "../api/client";
import { db } from "./db";

export async function cacheFazendas(): Promise<Fazenda[]> {
  try {
    const data = await get<Fazenda[]>("/fazendas");
    await db.fazendas.bulkPut(data);
    return data;
  } catch {
    return db.fazendas.toArray();
  }
}

export async function cacheAnimais(fazendaId: string): Promise<Animal[]> {
  try {
    const data = await get<Animal[]>(`/animais?fazenda_id=${fazendaId}`);
    await db.animais.bulkPut(data);
    return data;
  } catch {
    return db.animais.where("fazenda_id").equals(fazendaId).toArray();
  }
}

export async function cacheAnimal(animalId: string): Promise<Animal | null> {
  try {
    const data = await get<Animal>(`/animais/${animalId}`);
    await db.animais.put(data);
    return data;
  } catch {
    return (await db.animais.get(animalId)) ?? null;
  }
}

export interface ResultadoPost {
  resultado: unknown | null;
  enfileirado: boolean;
}

export async function postarComOutbox(
  path: string,
  payload: unknown,
): Promise<ResultadoPost> {
  try {
    const resultado = await post(path, payload);
    return { resultado, enfileirado: false };
  } catch {
    await db.outbox.add({
      local_id: crypto.randomUUID(),
      path,
      payload,
      criado_em: new Date().toISOString(),
      tentativas: 0,
    });
    return { resultado: null, enfileirado: true };
  }
}

export async function contarPendentes(): Promise<number> {
  return db.outbox.count();
}

export interface ResultadoSync {
  enviados: number;
  falhas: number;
}

export async function sincronizarOutbox(): Promise<ResultadoSync> {
  const itens = await db.outbox.orderBy("id").toArray();
  let enviados = 0;
  let falhas = 0;
  for (const item of itens) {
    try {
      await post(item.path, item.payload);
      await db.outbox.delete(item.id!);
      enviados++;
    } catch {
      await db.outbox.update(item.id!, {
        tentativas: (item.tentativas ?? 0) + 1,
      });
      falhas++;
    }
  }
  return { enviados, falhas };
}
