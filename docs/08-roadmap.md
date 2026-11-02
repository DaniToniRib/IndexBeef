# 08 · Roadmap

## Fase 0: Fundação (semanas 1–2)
- [x] Documentação e arquitetura
- [ ] Estrutura do repositório (monorepo) + `docker compose` funcionando
- [ ] CI básico (lint + testes)
- [ ] Gerar o PDF da placa ArUco

## Fase 1: Protótipo em casa (semanas 3–6)
Objetivo: **foto ou vídeo entra, ficha do animal sai**, com fotos e vídeos de Nelore de teste.

- [ ] Backend: CRUD de fazenda, lote e animal + upload de captura
- [ ] Worker: extração de frames, segmentação (YOLO-seg), filtro de qualidade
- [ ] Calibração ArUco
- [ ] **Tela de keypoints manual/semiautomática**
- [ ] Cálculo de medidas + caixa virtual + IPL
- [ ] Peso pela fórmula de referência
- [ ] Ficha do animal com a imagem anotada e a caixa desenhada
- [ ] Frontend PWA: câmera ao vivo com guia de silhueta, upload de vídeo e foto
- [ ] Funciona **offline** (notebook sem internet + celular no Wi-Fi local)
- [ ] Importação CSV: animais, DEPs e pesagens

**Critério de saída**: medir uma caixa de papelão ou um objeto de tamanho conhecido com erro < 3%, e processar 10 vídeos de Nelore de ponta a ponta.

## Fase 2: Teste de campo no Pantanal (semanas 7–8)
- [ ] Seguir o [protocolo de coleta](07-protocolo-coleta-campo.md)
- [ ] Coletar de 160 a 330 animais

**Critério de saída**: dataset completo (identificação + peso + vídeo) de pelo menos 150 animais.

## Fase 3: Primeiros modelos (semanas 9–14)
- [ ] Anotar os keypoints do dataset
- [ ] Fine-tuning da segmentação para Nelore
- [ ] Treinar o modelo de keypoints lateral (YOLO-pose ou RTMPose)
- [ ] Treinar o modelo de peso (LightGBM)
- [ ] Relatório de acurácia

**Metas**:
| Métrica | Meta |
|---|---|
| Erro das medidas lineares (× hipômetro) | < 3 cm |
| MAPE do peso (× balança) | < 5% |
| Keypoints: PCK@0.05 | > 85% |

## Fase 4: Índices (semanas 15–20)
- [ ] Frame score, ECC por imagem, EPMURAS assistido
- [ ] Índices Garrote, Reprodutor e Matriz (calibrados com o técnico)
- [ ] Ranking do lote, histórico, GMD e projeção de peso
- [ ] Acompanhamento mensal das matrizes prenhes

## Fase 5: Nuvem e escala
- [ ] Sincronização fazenda ↔ nuvem
- [ ] Painel remoto para o criador
- [ ] Registro de modelos e atualização automática das estações
- [ ] Usuários, papéis e várias fazendas

## Fase 6: Evoluções
- [ ] Câmera fixa no brete com avaliação automática na passagem + RFID
- [ ] Profundidade 3D (LiDAR / RealSense) para a caixa virtual real
- [ ] Inferência completa no celular
- [ ] Validação do índice matriz com o peso à desmama real dos bezerros (ciclo de 1 a 2 anos)
- [ ] Outras raças
