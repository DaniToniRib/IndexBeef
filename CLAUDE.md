# CLAUDE.md — IndexBeef

## Projeto
Sistema de avaliação morfológica de bovinos **Nelore (PO e CEIP)** por visão computacional: caixa virtual, medidas, peso estimado e índices de aptidão (garrote, reprodutor e matriz). O primeiro teste de campo será no **Pantanal**, que **não tem internet** → arquitetura **offline-first**.

**Leia a pasta `docs/` antes de implementar qualquer coisa.** Os documentos são a fonte da verdade:
- `docs/02-arquitetura.md`: componentes e decisões (ADRs)
- `docs/04-pipeline-visao.md`: pipeline, keypoints (IDs 0–17), fórmulas das medidas e da caixa virtual
- `docs/05-avaliacoes-e-indices.md`: peso, escores e índices
- `docs/06-modelo-de-dados.md`: tabelas
- `docs/08-roadmap.md`: fase atual e próximas tarefas
- `docs/09-stack-e-estrutura.md`: stack e estrutura de pastas

Se uma implementação divergir da documentação, **atualize o documento** no mesmo commit.

## Stack
- `apps/api`: Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
- `apps/worker`: Python, OpenCV, Ultralytics YOLO, RQ/Redis
- `apps/web`: React + Vite + TypeScript, PWA, Tailwind, Dexie (IndexedDB)
- Infra: Docker Compose (PostgreSQL, Redis, MinIO)

## Comandos
(atualizar conforme forem criados)
```bash
docker compose up -d            # sobe tudo
docker compose logs -f api      # logs da API
cd apps/api && pytest           # testes backend
cd apps/worker && pytest        # testes do pipeline
cd apps/web && npm test         # testes frontend
ruff check . && ruff format .   # lint/format Python
```

## Convenções
- Domínio em **português** (`animal`, `avaliacao`, `matriz`, `pesagem`); termos técnicos genéricos em inglês.
- Commits em português, no estilo Conventional Commits: `feat(worker): calibração ArUco`.
- Unidades: **cm, kg, graus**. Sufixo no nome quando houver ambiguidade (`peso_kg`, `altura_cm`).
- IDs são **UUID gerados no cliente** (necessário para o offline e o sync).
- Funções do pipeline são **puras e testáveis** (recebem arrays/dicts e retornam dicts), sem acessar o banco.
- Toda predição salva `confianca` e a versão do modelo/pipeline.

## Regras
- **Nunca** commitar fotos, vídeos, datasets ou pesos de modelos (`samples/`, `data/`, `*.pt`, `*.onnx` ficam no `.gitignore`).
- Pesos e limiares dos índices ficam **somente** em `config/indices.yaml`.
- Os índices são **apoio à decisão**: a UI sempre mostra a confiança e o aviso de triagem.
- Não inventar valores zootécnicos como se fossem fatos. Quando faltar referência, marque `# TODO: validar com zootecnista`.
- Escrever testes junto com cada módulo do pipeline (use keypoints/imagens sintéticas).
- Rodar os testes antes de dar uma tarefa como concluída.
