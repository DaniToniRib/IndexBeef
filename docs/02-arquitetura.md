# 02 · Arquitetura

## Princípio: offline-first

A fazenda funciona como uma **ilha autônoma**: captura, processa e mostra resultados sem internet. A nuvem serve para consolidar, treinar modelos e oferecer o painel remoto.

```
        FAZENDA (sem internet)                                NUVEM
┌────────────────────────────────────────────┐       ┌───────────────────────────┐
│ Celular/Tablet — PWA no navegador           │       │ Backend central           │
│  • câmera ao vivo + guia de silhueta        │       │  • Postgres consolidado   │
│  • modelo leve no aparelho (ONNX Web):      │       │  • treino de modelos (GPU)│
│    detecta o animal, avalia nitidez e pose  │       │  • registro de modelos    │
│  • fila local (IndexedDB) de fotos/vídeos   │       │  • painel do criador      │
└──────────────────┬─────────────────────────┘       └─────────────▲─────────────┘
                   │ Wi-Fi local (roteador na estação)              │
┌──────────────────▼─────────────────────────┐                     │
│ Estação de campo — notebook (GPU opcional)  │─────────────────────┘
│  docker compose:                            │   sincronização quando houver
│   • api      (FastAPI)                      │   sinal (Starlink / 4G)
│   • worker   (pipeline de visão)            │
│   • db       (PostgreSQL)                   │
│   • storage  (MinIO, compatível S3)         │
│   • queue    (Redis)                        │
│   • web      (frontend PWA servido local)   │
└────────────────────────────────────────────┘
```

O **mesmo `docker compose`** roda no notebook do desenvolvedor, na estação de campo e (com outra configuração) na nuvem.

## Componentes

### 1. App de captura (frontend PWA)
- React + Vite (ou Next.js em modo estático), instalável no celular.
- Acessa a câmera via `getUserMedia` (ao vivo) e permite upload de vídeo e foto.
- Roda no próprio aparelho um **modelo leve de detecção** (ONNX Runtime Web) para:
  - mostrar se o animal está inteiro no quadro;
  - avisar se a imagem está desfocada ou se o animal não está de lado;
  - capturar automaticamente o melhor momento.
- Guarda a captura em **IndexedDB** e envia para a estação quando ela estiver acessível.

### 2. API (backend)
- **FastAPI** (Python).
- Cadastro de fazenda, lote e animal; recebe as capturas; consulta os resultados.
- Envia as tarefas pesadas para a fila.

### 3. Worker de visão
- Consome a fila (Celery ou RQ + Redis).
- Executa o [pipeline de visão](04-pipeline-visao.md).
- Funciona em CPU (mais lento) ou GPU.

### 4. Armazenamento
- **PostgreSQL**: dados estruturados (ver [modelo de dados](06-modelo-de-dados.md)).
- **MinIO**: imagens, vídeos, máscaras e frames anotados.

### 5. Sincronização fazenda ↔ nuvem
- Cada registro tem um `uuid` gerado na origem, `updated_at` e `origem` (estação).
- Envio **incremental**: só o que mudou desde o último sync.
- As mídias sobem em segundo plano, primeiro em versão reduzida, e o original vai depois, se a banda permitir.
- Conflitos: o último a escrever vence nos dados cadastrais. Avaliações nunca são sobrescritas, só acrescentadas.

### 6. Nuvem
- Mesmo backend, mais:
  - **treino de modelos** com os dados de todas as fazendas;
  - **registro de modelos** (MLflow), que publica novas versões para as estações;
  - painel web para o criador acompanhar de qualquer lugar.

## Fluxo de uma avaliação

```
1. Vaqueiro identifica o animal (brinco/RGN digitado, leitura de RFID ou QR)
2. Aponta a câmera: o app guia o enquadramento e grava 5–10 s de vídeo lateral
3. Opcional: foto traseira
4. App envia para a estação (ou guarda na fila se ela estiver offline)
5. Worker processa: frames → segmentação → keypoints → medidas → índices
6. Técnico revisa os pontos na tela (pode arrastar e corrigir)
7. Resultado: ficha do animal com caixa virtual, medidas, peso estimado e índices
```

## Decisões de arquitetura (ADR resumidas)

| # | Decisão | Motivo |
|---|---|---|
| ADR-01 | PWA em vez de app nativo no MVP | Uma base só (Android/iOS/desktop), sem loja, rápido de iterar. Migrar para React Native se for preciso usar LiDAR/RFID nativo. |
| ADR-02 | Python/FastAPI no backend | Mesmo ecossistema do ML (PyTorch, OpenCV). |
| ADR-03 | Docker Compose na fazenda | Instalação reproduzível e sem depender de internet. |
| ADR-04 | Processamento pesado na estação, não no celular | Celulares variam muito; a estação garante consistência. |
| ADR-05 | Vídeo como entrada preferencial | Vários frames dão mediana das medidas e medem a confiança. |
| ADR-06 | Marcador ArUco para calibração | Barato, preciso e funciona com qualquer câmera. |
| ADR-07 | Keypoints semiautomáticos no início | Não há dataset; as correções do técnico geram o dataset. |
