import { beforeEach, describe, expect, it, vi } from "vitest";
import { get, post } from "../api/client";
import { db } from "./db";
import {
  cacheAnimais,
  cacheFazendas,
  contarPendentes,
  postarComOutbox,
  sincronizarOutbox,
} from "./sync";

vi.mock("../api/client", () => ({ get: vi.fn(), post: vi.fn() }));

const mockGet = vi.mocked(get);
const mockPost = vi.mocked(post);

const fazenda = { id: "f1", nome: "Fazenda Teste", tipo: "fazenda" as const };
const animal = {
  id: "a1",
  fazenda_id: "f1",
  brinco: "001",
  ceip: false,
  sexo: "M" as const,
  situacao: "ativo",
  raca: "Nelore",
};

beforeEach(async () => {
  vi.clearAllMocks();
  await db.fazendas.clear();
  await db.animais.clear();
  await db.outbox.clear();
});

describe("cacheFazendas", () => {
  it("retorna dados da API e persiste no IndexedDB", async () => {
    mockGet.mockResolvedValueOnce([fazenda]);
    const result = await cacheFazendas();
    expect(result).toEqual([fazenda]);
    expect(await db.fazendas.toArray()).toEqual([fazenda]);
  });

  it("retorna cache local quando a API falha", async () => {
    await db.fazendas.put(fazenda);
    mockGet.mockRejectedValueOnce(new Error("offline"));
    const result = await cacheFazendas();
    expect(result).toEqual([fazenda]);
  });
});

describe("cacheAnimais", () => {
  it("retorna dados da API e persiste no IndexedDB", async () => {
    mockGet.mockResolvedValueOnce([animal]);
    const result = await cacheAnimais("f1");
    expect(result).toEqual([animal]);
    expect(await db.animais.toArray()).toEqual([animal]);
  });

  it("retorna cache local quando a API falha", async () => {
    await db.animais.put(animal);
    mockGet.mockRejectedValueOnce(new Error("offline"));
    const result = await cacheAnimais("f1");
    expect(result).toEqual([animal]);
  });
});

describe("postarComOutbox", () => {
  it("posta na API quando online e retorna resultado", async () => {
    mockPost.mockResolvedValueOnce({ id: "av1" });
    const result = await postarComOutbox("/avaliacoes", { animal_id: "a1" });
    expect(result.enfileirado).toBe(false);
    expect(result.resultado).toEqual({ id: "av1" });
    expect(await db.outbox.count()).toBe(0);
  });

  it("enfileira no outbox quando a API falha", async () => {
    mockPost.mockRejectedValueOnce(new Error("offline"));
    const result = await postarComOutbox("/avaliacoes", { animal_id: "a1" });
    expect(result.enfileirado).toBe(true);
    expect(result.resultado).toBeNull();
    expect(await db.outbox.count()).toBe(1);
  });
});

describe("contarPendentes", () => {
  it("retorna zero quando outbox está vazio", async () => {
    expect(await contarPendentes()).toBe(0);
  });

  it("retorna o número de itens no outbox", async () => {
    const base = { path: "/avaliacoes", payload: {}, criado_em: new Date().toISOString(), tentativas: 0 };
    await db.outbox.add({ ...base, local_id: "l1" });
    await db.outbox.add({ ...base, local_id: "l2" });
    expect(await contarPendentes()).toBe(2);
  });
});

describe("sincronizarOutbox", () => {
  it("envia itens e limpa o outbox em caso de sucesso", async () => {
    await db.outbox.add({ local_id: "l1", path: "/avaliacoes", payload: { animal_id: "a1" }, criado_em: new Date().toISOString(), tentativas: 0 });
    mockPost.mockResolvedValueOnce({ id: "av1" });
    const result = await sincronizarOutbox();
    expect(result.enviados).toBe(1);
    expect(result.falhas).toBe(0);
    expect(await db.outbox.count()).toBe(0);
  });

  it("incrementa tentativas quando o envio falha e mantém o item", async () => {
    await db.outbox.add({ local_id: "l1", path: "/avaliacoes", payload: { animal_id: "a1" }, criado_em: new Date().toISOString(), tentativas: 0 });
    mockPost.mockRejectedValueOnce(new Error("offline"));
    const result = await sincronizarOutbox();
    expect(result.enviados).toBe(0);
    expect(result.falhas).toBe(1);
    const item = (await db.outbox.toArray())[0];
    expect(item.tentativas).toBe(1);
  });
});
