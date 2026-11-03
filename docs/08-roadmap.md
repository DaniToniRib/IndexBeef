# 08 · Roadmap

## Fase 0: Fundação (semanas 1–2)
- [x] Documentação e arquitetura
- [x] Estrutura do repositório (monorepo) + `docker compose` funcionando
- [x] CI básico (lint + testes) — GitHub Actions: api/worker/web em paralelo
- [x] Gerar o PDF da placa ArUco — `hardware/placa-aruco-40cm-id0.pdf` (e id1 e A3)

## Fase 1: Protótipo em casa (semanas 3–6)
Objetivo: **foto ou vídeo entra, ficha do animal sai**, com fotos e vídeos de Nelore de teste.

- [x] Backend: CRUD de fazenda, lote e animal + upload de captura (`POST /capturas/extrair-frame`)
- [x] Worker: extração de frames + filtro Laplaciano; task `preparar_frames_avaliacao` integrada via `POST /capturas` (tipo='video' enfileira RQ; ~~YOLO-seg~~ bloqueado — Fase 2)
- [x] Calibração ArUco
- [x] **Tela de keypoints manual/semiautomática** (`NovaAvaliacao` com canvas)
- [x] Cálculo de medidas + caixa virtual + IPL (quando `area_tronco_cm2` disponível)
- [x] Peso pela fórmula de referência
- [x] Ficha do animal com imagem (quando MinIO ativo e captura disponível)
- [x] Frontend PWA: câmera ao vivo com guia de silhueta (`CameraCaptura`), upload de vídeo e foto
- [x] Funciona **offline** (IndexedDB / Dexie — `offline/db.ts`, `sync.ts`, `StatusOffline.tsx`)
- [x] Importação CSV: animais (`POST /animais/importar-csv`) e pesagens (`POST /pesagens/importar-csv`)
- [x] Importação CSV: DEPs (`POST /animais/importar-csv-deps`, tabela `dados_geneticos`)

**Critério de saída**: medir uma caixa de papelão ou um objeto de tamanho conhecido com erro < 3%, e processar 10 vídeos de Nelore de ponta a ponta.

## Fase 2: Teste de campo no Pantanal (semanas 7–8)
- [ ] Seguir o [protocolo de coleta](07-protocolo-coleta-campo.md)
- [ ] Coletar de 160 a 330 animais

### Preparação de campo (implementado 2026-11-03)
- [x] Notas do técnico: ECC e EPMURAS por avaliação (`escore_avaliacao`, campo na UI)
- [x] Medidas manuais de referência (~1:3): hipômetro/fita/paquímetro (`medida_avaliacao` colunas `*_manual_cm`)
- [x] Eventos reprodutivos: cobertura, IATF, diagnóstico de gestação, parto, aborto, desmama (`evento_reprodutivo`, router `/eventos-reprodutivos`)
- [x] Exame andrológico de touros (`exame_andrologico`, router `/exames-andrologicos`)
- [x] DEPs por animal (`dados_geneticos`, router `POST /animais/importar-csv-deps`)

**Critério de saída**: dataset completo (identificação + peso + vídeo) de pelo menos 150 animais.

## Fase 3: Primeiros modelos (semanas 9–14)
- [x] Exportação COCO para anotação de keypoints (`GET /avaliacoes/exportar-coco`)
- [x] `modelo_versao`: tabela + API de registro e ativação de modelos treinados
- [x] Script de treino LightGBM (`ml/train/train_peso_lightgbm.py`)
- [x] Módulo de inferência YOLO-pose (`indexbeef_vision/keypoints_inference.py`) — ativo quando modelo disponível
- [x] Relatório de acurácia (`GET /relatorio/acuracia`, `GET /relatorio/pesos`)
- [ ] Fine-tuning da segmentação para Nelore — aguarda dataset Fase 2
- [ ] Treinar modelo de keypoints lateral (YOLO-pose) — aguarda dataset Fase 2
- [ ] Treinar modelo de peso (LightGBM) — aguarda dataset Fase 2
- [ ] Relatório de acurácia com dados reais — aguarda dataset Fase 2

**Metas**:
| Métrica | Meta |
|---|---|
| Erro das medidas lineares (× hipômetro) | < 3 cm |
| MAPE do peso (× balança) | < 5% |
| Keypoints: PCK@0.05 | > 85% |

## Fase 4: Índices (semanas 15–20)
- [x] Frame score, ECC por imagem, EPMURAS assistido
- [x] Índices Garrote, Reprodutor e Matriz (calibrados com o técnico)
- [x] Ranking do lote, histórico, GMD e projeção de peso
- [x] Acompanhamento mensal das matrizes prenhes

### Implementado 2026-11-03
- `apps/api/alembic/versions/0011_fase4_indices.py` — migration: `explicacao JSON` e `modelo_versao_id UUID FK` em `predicao_avaliacao`
- `apps/api/app/models/predicao_avaliacao.py` — campos `explicacao` e `modelo_versao_id` adicionados ao modelo
- `apps/api/app/services/indices_service.py` — funções puras: `calcular_frame_score`, `sugerir_epmuras`, `calcular_gmd`, `calcular_projecao_brody`, `calcular_indice`, `montar_componentes_garrote/reprodutor/matriz`; carrega `config/indices.yaml` uma vez ao importar
- `apps/api/app/routers/indices.py` — 5 endpoints: `POST /indices/avaliacoes/{id}/calcular`, `GET /lotes/{id}/ranking`, `GET /lotes/{id}/matrizes-prenhes`, `GET /animais/{id}/gmd`, `GET /animais/{id}/projecao-peso`
- `apps/api/app/schemas/avaliacao.py` — novos schemas: `IndiceResultadoResponse`, `RankingResponse`, `MatrizPrenheResponse`, `GmdResponse`, `ProjecaoPesoResponse`
- `apps/api/tests/test_fase4.py` — 16 testes, todos verdes
- `apps/web/src/pages/NovaAvaliacao.tsx` — dispara `POST /indices/…/calcular` após envio; caixa colapsável "Frame Score & EPMURAS sugerido"
- `apps/web/src/pages/FichaAnimal.tsx` — cards de índices com top-3 componentes da `explicacao`
- `apps/web/src/pages/RankingLote.tsx` — tabela de ranking com barra de progresso, dropdown de índice, loading e empty state
- `apps/web/src/App.tsx` — rota `ranking-lote` → `<RankingLote />`

## Fase 5: Nuvem e escala
- [x] Sincronização fazenda ↔ nuvem
- [x] Painel remoto para o criador
- [x] Registro de modelos e atualização automática das estações
- [x] Usuários, papéis e várias fazendas

### Implementado 2026-11-03
- `apps/api/alembic/versions/0012_fase5_auth.py` — migration: tabelas `usuario` e `fazenda_usuario`
- `apps/api/app/models/usuario.py` — modelo `Usuario` (email, nome, senha_hash, ativo)
- `apps/api/app/models/fazenda_usuario.py` — modelo `FazendaUsuario` (fazenda_id, usuario_id, papel)
- `apps/api/app/core/auth.py` — funções `hash_senha`, `verificar_senha`, `criar_token`, `decodificar_token` (bcrypt + PyJWT HS256, 7 dias)
- `apps/api/app/schemas/usuario.py` — schemas `UsuarioRegistrar`, `UsuarioLogin`, `UsuarioRead`, `TokenResponse`
- `apps/api/app/routers/auth.py` — 3 endpoints: `POST /auth/registrar`, `POST /auth/login`, `GET /auth/me`; endpoints existentes não foram modificados
- `apps/api/app/routers/sync.py` — `POST /sync/push` (upsert multi-tabela), `GET /sync/pull` (pull incremental desde timestamp)
- `apps/api/app/routers/dashboard.py` — `GET /fazendas/{id}/painel-remoto` (totais, últimas avaliações, alertas ECC, peso médio por lote)
- `apps/api/app/routers/modelo_versao.py` — `GET /modelos-versao/verificar-atualizacao` (movido antes de `/{modelo_id}` para evitar conflito de rota)
- `apps/api/app/main.py` — auth e sync registrados
- `apps/api/tests/test_fase5.py` — 17 testes, todos verdes (total geral: 134)
- `apps/worker/scripts/atualizar_modelos.py` — script standalone para verificar e baixar modelos ONNX atualizados
- `apps/web/src/pages/PainelRemoto.tsx` — componente React com cards de totais, tabela de avaliações, alertas ECC e peso médio por lote
- `apps/web/src/App.tsx` — rota `painel-remoto` → `<PainelRemoto />`

## Fase 6: Evoluções
- [ ] Câmera fixa no brete com avaliação automática na passagem + RFID
- [ ] Profundidade 3D (LiDAR / RealSense) para a caixa virtual real
- [x] Inferência completa no celular
- [ ] Validação do índice matriz com o peso à desmama real dos bezerros (ciclo de 1 a 2 anos)
- [ ] Outras raças

### Implementado 2026-11-03 (Inferência completa no celular)
- `ml/train/exportar_onnx.py` — script para exportar modelo YOLO-pose para ONNX via ultralytics
- `apps/worker/indexbeef_vision/onnx_inference.py` — módulo `carregar_sessao_onnx` + `predizer_keypoints_onnx`; alternativa ao PyTorch para dispositivos sem GPU; retorna mesma estrutura de keypoints
- `apps/web/src/workers/keypointsWorker.ts` — Web Worker para inferência de keypoints no browser via ONNX Runtime Web; placeholder ativo quando modelo estiver disponível em `/modelos/keypoints.onnx`
- `apps/web/package.json` — `onnxruntime-web ^1.19.0` adicionado a devDependencies
