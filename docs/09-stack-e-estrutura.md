# 09 · Stack e estrutura do repositório

## Stack

| Camada | Tecnologia | Versão alvo |
|---|---|---|
| Frontend | React + Vite + TypeScript, PWA (`vite-plugin-pwa`) | Node 20+ |
| UI | Tailwind CSS | |
| Estado offline | IndexedDB (Dexie.js) | |
| Inferência no aparelho | ONNX Runtime Web | |
| Backend | Python + **FastAPI** + SQLAlchemy 2 + Alembic | Python 3.11+ |
| Fila | Redis + **RQ** (mais simples) ou Celery | |
| Visão | OpenCV, **Ultralytics YOLO**, SAM 2, ffmpeg | |
| ML | PyTorch, LightGBM, scikit-learn | |
| Experimentos | MLflow | |
| Banco | PostgreSQL 16 | |
| Arquivos | MinIO (S3) | |
| Infra | Docker + Docker Compose | |
| Testes | pytest (back), Vitest + Playwright (front) | |
| Qualidade | ruff, mypy, eslint, prettier, pre-commit | |
| CI | GitHub Actions | |

## Estrutura do repositório (monorepo)

```
IndexBeef/
├── README.md
├── CLAUDE.md                  # instruções para o Claude Code
├── docker-compose.yml         # estação de campo / dev
├── .env.example
├── docs/                      # esta documentação
│
├── apps/
│   ├── api/                   # FastAPI
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── core/          # config, segurança, db
│   │   │   ├── models/        # SQLAlchemy
│   │   │   ├── schemas/       # Pydantic
│   │   │   ├── routers/       # fazendas, animais, avaliacoes, capturas, importacao
│   │   │   └── services/
│   │   ├── alembic/
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── worker/                # pipeline de visão
│   │   ├── indexbeef_vision/
│   │   │   ├── frames.py       # extração de frames
│   │   │   ├── segmentation.py
│   │   │   ├── tracking.py
│   │   │   ├── quality.py      # score de qualidade
│   │   │   ├── keypoints.py
│   │   │   ├── calibration.py  # ArUco + homografia
│   │   │   ├── measurements.py
│   │   │   ├── virtual_box.py
│   │   │   ├── indices.py
│   │   │   └── pipeline.py     # orquestração
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── web/                   # PWA React
│       ├── src/
│       │   ├── pages/          # Captura, Animais, Ficha, RevisaoKeypoints, Lotes
│       │   ├── components/
│       │   ├── camera/         # getUserMedia, guia de silhueta, validação
│       │   ├── offline/        # Dexie, fila de envio
│       │   └── api/
│       └── package.json
│
├── ml/                        # treino (fora do runtime)
│   ├── notebooks/
│   ├── datasets/              # scripts (nunca os dados no git)
│   └── train/
│
├── config/
│   └── indices.yaml           # pesos e limiares dos índices
│
├── hardware/
│   └── gerar_placa_aruco.py
│
└── .github/workflows/ci.yml
```

## Convenções
- **Idioma**: domínio em português (`animal`, `avaliacao`, `matriz`); termos técnicos genéricos em inglês (`pipeline`, `frame`). Commits em português.
- **Unidades**: sempre **cm**, **kg**, **graus**, explícitas no nome quando houver ambiguidade (`peso_kg`).
- **IDs**: UUID gerado no cliente (necessário para o modo offline).
- **Mídias nunca no git**: ficam no MinIO, e os datasets são versionados à parte (DVC, em fase futura).
- **Pesos e limiares** de índices sempre em `config/indices.yaml`, nunca fixos no código.

## Docker Compose (serviços)

| Serviço | Porta | Função |
|---|---|---|
| `web` | 5173 / 80 | PWA |
| `api` | 8000 | FastAPI (docs em `/docs`) |
| `worker` | — | Pipeline de visão |
| `db` | 5432 | PostgreSQL |
| `redis` | 6379 | Fila |
| `minio` | 9000 / 9001 | Arquivos + console |
