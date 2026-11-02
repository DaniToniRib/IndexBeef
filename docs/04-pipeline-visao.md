# 04 · Pipeline de visão computacional

## Visão geral

```
Entrada (foto | vídeo | stream)
  │
  ├─ 1. Extração de frames ............ ffmpeg (ex.: 5 fps)
  ├─ 2. Detecção + segmentação ......... YOLO-seg (classe "cow") → refino com SAM 2
  ├─ 3. Rastreamento ................... ByteTrack (vários animais no vídeo)
  ├─ 4. Filtro de qualidade ............ nitidez, pose lateral, corpo inteiro, placa visível
  ├─ 5. Seleção dos N melhores frames .. N = 5 a 10
  ├─ 6. Keypoints anatômicos ........... modelo de pose + correção manual
  ├─ 7. Calibração px→cm ............... ArUco + homografia
  ├─ 8. Medidas por frame .............. geometria entre keypoints + máscara
  ├─ 9. Agregação ...................... mediana + desvio (= confiança)
  └─ 10. Caixa virtual + índices ....... ver doc 05
```

## 1. Extração de frames
- Vídeo: `ffmpeg -i entrada.mp4 -vf fps=5 frames/%04d.jpg`.
- Ao vivo: o app já envia os frames selecionados.
- Foto: tratada como um vídeo de um frame só.

## 2. Detecção e segmentação
- **Início sem treino**: o YOLO pré-treinado no COCO já tem a classe `cow`. Serve para detectar e gerar a máscara inicial.
- **Refino**: SAM 2 com a caixa do YOLO como *prompt*, para ter uma máscara mais precisa no contorno.
- **Depois do teste de campo**: fine-tuning com imagens de Nelore anotadas (pelagem clara, cupim, barbela).

## 3. Rastreamento
- Em vídeo de corredor com vários animais, usar **ByteTrack** para manter o ID de cada animal entre os frames.
- Associar o ID rastreado ao animal identificado (brinco digitado ou RFID lido naquele momento).

## 4–5. Filtro de qualidade e seleção
Pontuação de cada frame (0–1):

```
score = 0.30·nitidez + 0.25·lateralidade + 0.20·corpo_inteiro + 0.15·placa_visivel + 0.10·estabilidade
```

Ficam os N frames com maior score, com espaçamento mínimo entre eles para evitar frames quase idênticos.

## 6. Keypoints anatômicos (Nelore)

### Vista lateral: 18 pontos

| ID | Ponto | Uso |
|---|---|---|
| 0 | Focinho | Orientação |
| 1 | Nuca | Comprimento de pescoço |
| 2 | **Topo do cupim** | Tamanho de cupim (sexualidade/caracterização racial) |
| 3 | **Cernelha** (atrás do cupim) | Altura de cernelha |
| 4 | Meio do dorso | Linha de dorso |
| 5 | Lombo | Linha de dorso |
| 6 | **Ílio** (ponta da anca) | Altura de garupa, comprimento e inclinação de garupa |
| 7 | **Ísquio** (ponta da nádega) | Comprimento corporal, comprimento e inclinação de garupa |
| 8 | Inserção da cauda | Garupa |
| 9 | **Ponta da espádua** | Comprimento corporal |
| 10 | Cilha superior (dorso, atrás da paleta) | Profundidade torácica |
| 11 | Cilha inferior (esterno) | Profundidade torácica |
| 12 | **Umbigo / bainha** | Tamanho do umbigo |
| 13 | Ponto mais baixo do ventre | Capacidade corporal |
| 14 | Joelho (anterior) | Aprumos |
| 15 | Casco anterior | Aprumos, altura |
| 16 | Jarrete | Aprumos (ângulo do jarrete) |
| 17 | Casco posterior | Aprumos, altura |

### Vista traseira: 8 pontos
Ílio esquerdo e direito, trocânter esquerdo e direito, ísquio esquerdo e direito, jarrete esquerdo e direito.

### Estratégia sem dataset
1. **Fase 0**: o técnico **clica nos pontos** na tela (cerca de 30 s por animal). O sistema já calcula tudo.
2. **Fase 1**: com 300 a 500 animais anotados, treina-se o primeiro modelo de pose (YOLO-pose ou RTMPose).
3. **Fase 2**: o modelo sugere os pontos, o técnico só corrige, e cada correção alimenta o dataset (*active learning*).

Formato de anotação: **COCO Keypoints**. Ferramenta auxiliar: CVAT ou Label Studio.

## 7. Calibração
- Detectar o marcador ArUco (`cv2.aruco.ArucoDetector`).
- Calcular a **homografia** do plano da placa, que corrige perspectiva e escala.
- Como o animal está aproximadamente no plano da placa, as medidas são projetadas nesse plano.
- Com duas placas, interpolar a escala ao longo do comprimento do animal.
- Registrar `px_por_cm` e o erro de reprojeção (qualidade da calibração).

## 8. Medidas

| Medida | Cálculo |
|---|---|
| Altura de cernelha (AC) | Distância vertical da cernelha (3) até a linha do chão (cascos 15/17) |
| Altura de garupa (AG) | Distância vertical do ílio (6) até o chão |
| Comprimento corporal (CC) | Distância da ponta da espádua (9) ao ísquio (7) |
| Profundidade torácica (PT) | Distância da cilha superior (10) à inferior (11) |
| Comprimento de garupa (CG) | Distância do ílio (6) ao ísquio (7) |
| Inclinação de garupa (IG) | Ângulo da reta ílio→ísquio com a horizontal (graus) |
| Altura do cupim | Distância do topo do cupim (2) à cernelha (3) |
| Distância umbigo–chão | Altura do umbigo (12) até o chão |
| Largura de garupa (LG) | Vista traseira: distância entre os ílios ou entre os trocânteres |
| Ângulo do jarrete | Ângulo formado por ílio/trocânter, jarrete (16) e casco (17) |
| Área lateral do tronco | Área da máscara entre a espádua e o ísquio (cm²) |
| Perímetro torácico estimado (PTe) | Elipse com eixos PT e largura de tórax (vista dorsal ou traseira, ou razão média) |

## 9. Agregação
- Para cada medida: **mediana** dos N frames.
- **Confiança** = 1 − (coeficiente de variação normalizado), combinada com a qualidade da calibração.
- Medidas com confiança baixa aparecem em amarelo e pedem uma nova captura.

## 10. Caixa virtual

```
            ┌───────────────── C (comprimento corporal) ─────────────────┐
            │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ ▲
            │ ░░░░░░░░░ silhueta do tronco ░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │ P (profundidade)
            │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ ▼
            └───────────────────────────────────────────────────────────┘
                              + L (largura, vista traseira)
```

- **Caixa** = C × P × L (cm³), equivalente a um volume aparente.
- **Índice de preenchimento lateral (IPL)** = área da silhueta do tronco ÷ (C × P). Quanto mais próximo de 1, mais "cheio" é o animal (costela arqueada, flanco cheio, menos "barriga vazia").
- **Índice de compacidade** = PT ÷ AC. Animais profundos em relação à altura tendem a ser mais **precoces**.
- **Índice de comprimento** = CC ÷ AC. Indica espaço para carcaça.
- A caixa é **desenhada sobre a imagem** no relatório.

## Saída do pipeline (JSON)

```json
{
  "avaliacao_id": "uuid",
  "versao_pipeline": "0.1.0",
  "frames_usados": 7,
  "calibracao": { "px_por_cm": 4.12, "erro_reproj_px": 0.8 },
  "medidas_cm": {
    "altura_cernelha": { "valor": 128.4, "confianca": 0.91 },
    "altura_garupa":   { "valor": 131.0, "confianca": 0.93 },
    "comprimento_corporal": { "valor": 142.7, "confianca": 0.88 },
    "profundidade_toracica": { "valor": 63.5, "confianca": 0.85 },
    "comprimento_garupa": { "valor": 46.2, "confianca": 0.84 },
    "largura_garupa": { "valor": 44.0, "confianca": 0.80 }
  },
  "angulos_graus": { "inclinacao_garupa": 11.5, "jarrete": 148.0 },
  "caixa_virtual": { "C": 142.7, "P": 63.5, "L": 44.0, "volume_l": 398.7, "ipl": 0.81 },
  "imagens": { "lateral_anotada": "s3://.../lat.jpg", "traseira_anotada": "s3://.../tras.jpg" }
}
```
