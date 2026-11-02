# 🐂 IndexBeef

**Avaliação morfológica de bovinos Nelore (PO e CEIP) por visão computacional.**

O IndexBeef analisa fotos, vídeos ou a câmera ao vivo de um animal e gera:

- **Caixa virtual**: comprimento × altura × profundidade/largura do animal, com o índice de preenchimento (enchimento de carcaça).
- **Medidas lineares**: altura de cernelha e de garupa, comprimento corporal, profundidade torácica, largura e inclinação de garupa.
- **Peso estimado** e **projeção de peso futuro**.
- **Escores**: Frame, ECC (condição corporal) e EPMURAS assistido.
- **Índices de aptidão**:
  - 🥩 **Garrote/Bezerro**: potencial de enchimento de carcaça e ganho de peso.
  - 🐂 **Reprodutor**: estrutura, aprumos, umbigo/bainha e genética.
  - 🐄 **Matriz**: capacidade de gestar e desmamar bons bezerros (capacidade corporal, garupa, umbigo, ECC na gestação e DEPs maternas).

> ⚠️ O IndexBeef é uma ferramenta de **triagem e apoio à decisão**. Não substitui exame andrológico, diagnóstico de gestação, avaliação de técnico habilitado nem avaliação genética oficial.

---

## Status

🟡 **Fase 0: Documentação e arquitetura.** Ainda não há código.

O primeiro teste de campo será em fazendas no **Pantanal** com gado **Nelore CEIP**.

---

## Documentação

| # | Documento | Conteúdo |
|---|---|---|
| 01 | [Visão geral](docs/01-visao-geral.md) | Problema, objetivo, público e escopo |
| 02 | [Arquitetura](docs/02-arquitetura.md) | Arquitetura offline-first (fazenda + nuvem) |
| 03 | [Captura](docs/03-captura.md) | Câmera ao vivo, vídeo, foto e calibração |
| 04 | [Pipeline de visão](docs/04-pipeline-visao.md) | Segmentação, keypoints, medidas e caixa virtual |
| 05 | [Avaliações e índices](docs/05-avaliacoes-e-indices.md) | Peso, Frame, ECC, EPMURAS, garrote, reprodutor e matriz |
| 06 | [Modelo de dados](docs/06-modelo-de-dados.md) | Entidades e esquema do banco |
| 07 | [Protocolo de coleta em campo](docs/07-protocolo-coleta-campo.md) | Como coletar os dados no Pantanal |
| 08 | [Roadmap](docs/08-roadmap.md) | Fases, entregas e critérios de sucesso |
| 09 | [Stack e estrutura do repositório](docs/09-stack-e-estrutura.md) | Tecnologias e organização das pastas |
| 10 | [Desenvolvimento com Claude Code no VS Code](docs/10-desenvolvimento-vscode-claude.md) | Ambiente e fluxo de trabalho |
| — | [Glossário](docs/glossario.md) | Termos zootécnicos e técnicos |

---

## Visão rápida da arquitetura

```
Celular/Tablet (PWA) ──Wi-Fi local──► Estação de campo (notebook + Docker)
  câmera ao vivo / vídeo / foto         FastAPI + Worker de visão + Postgres + MinIO
  pré-validação no aparelho             funciona 100% offline
                                              │
                                              └──sync (Starlink/4G)──► Nuvem
                                                                       painel, treino de modelos
```

---

## Licença

A definir. Por enquanto, repositório privado.
