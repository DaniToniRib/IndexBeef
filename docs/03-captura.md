# 03 · Captura de imagens

A qualidade da captura determina a qualidade da avaliação. Este documento define **como** capturar.

## Modos de entrada

| Modo | Uso | Observação |
|---|---|---|
| **Câmera ao vivo** | Uso normal no curral | O app guia, valida e captura automaticamente os melhores frames |
| **Vídeo gravado** | Gravado antes, com outro aparelho, drone ou câmera fixa | Upload; o sistema extrai e seleciona os frames |
| **Foto** | Rápido, ou quando só há foto | Menos robusto; o ideal são 2 ou 3 fotos por vista |

Todos os modos entram no **mesmo pipeline** (ver [04](04-pipeline-visao.md)).

## Vistas

| Vista | Obrigatória? | O que mede |
|---|---|---|
| **Lateral** (preferencialmente o lado esquerdo) | ✅ Sim | Altura, comprimento, profundidade, linha de dorso, garupa (inclinação), umbigo, aprumos laterais |
| **Traseira** | Recomendada | Largura de garupa, musculatura do posterior, aprumos traseiros |
| **Dorsal** (de cima) | Opcional | Largura de tórax e de lombo (drone ou câmera presa no alto do brete) |
| **Frontal** | Opcional | Aprumos dianteiros |

## Posição ideal do animal (vista lateral)

- Em estação, com os **quatro membros apoiados** e os da frente alinhados com os de trás.
- Cabeça em posição natural (nem abaixada pastando, nem levantada).
- Câmera **perpendicular** ao animal, na **altura do meio do corpo** (aproximadamente 1,0–1,2 m).
- Distância de 3 a 6 m, com o animal inteiro no quadro e uma margem pequena.
- Fundo contrastante quando possível. Nelore branco contra cerca branca ou céu claro atrapalha a segmentação.
- Evitar contraluz (sol atrás do animal).

## Calibração (pixel → centímetro)

Sem calibração não existe medida em centímetros. Opções, em ordem de prioridade:

1. **Placa ArUco** (recomendada no MVP)
   - Placa rígida (PVC ou ACM) de **40 × 40 cm**, com o marcador ArUco impresso.
   - Fixada **no mesmo plano do animal**, por exemplo na lateral do tronco ou do corredor, na altura do flanco.
   - O sistema detecta a placa e calcula px/cm e a correção de perspectiva.
   - Para ter mais precisão, usar **duas placas** (frente e trás do corredor).
2. **Câmera fixa calibrada**: suporte fixo a uma distância conhecida do corredor, com calibração feita uma vez.
3. **Profundidade (LiDAR / RealSense)**: medida 3D direta. É a melhor para a caixa virtual, mas exige hardware específico (fase posterior).

> 📌 **PDF da placa**: gerado por `hardware/gerar_placa_aruco.py` (OpenCV `cv2.aruco`, dicionário `DICT_4X4_50`, IDs 0 e 1).
>
> O PDF é emitido **no tamanho físico real** (40×40 cm + 2 cm de margem/*quiet zone*), para que a gráfica/plotter reproduza as dimensões sem reescalonamento. Nunca imprimir "ajustar à página".
>
> Comandos:
> ```bash
> pip install -r hardware/requirements.txt
> python hardware/gerar_placa_aruco.py --id 0  # → hardware/placa-aruco-40cm-id0.pdf
> python hardware/gerar_placa_aruco.py --id 1  # → hardware/placa-aruco-40cm-id1.pdf
> # Para bancada (não usar em campo):
> python hardware/gerar_placa_aruco.py --formato a3 --id 0
> ```

## Montagem recomendada no curral

```
            Placa ArUco (ID 0)              Placa ArUco (ID 1)
                 ▼                                ▼
   ═════════════╪════════════════════════════════╪══════════  ← cerca do corredor/tronco
                         🐂  (animal parado)
   ──────────────────────────────────────────────────────────

                         📱  câmera a ~4 m, altura ~1,1 m
                         (tripé ou marca no chão)
```

- Marcar no chão o **ponto fixo** da câmera para padronizar.
- Se possível, usar **tripé**: medidas repetíveis valem mais do que mobilidade.

## Validação em tempo real no app

O modelo leve no aparelho avalia cada frame e mostra:

| Indicador | Regra (inicial, a ajustar) |
|---|---|
| 🟢 Animal inteiro | A caixa do animal não toca as bordas da imagem |
| 🟢 Lateral | Razão largura/altura da caixa > 1,4 |
| 🟢 Nítido | Variância do Laplaciano acima do limiar |
| 🟢 Placa visível | Marcador ArUco detectado |
| 🟢 Parado | Pouco movimento entre frames consecutivos |

Quando todos estiverem verdes por cerca de 1 s, o app **captura automaticamente** (frames + trecho de vídeo).

## Identificação do animal

- MVP: digitar o **número do brinco** ou o **RGN** (com busca no cadastro importado).
- Depois: leitura de **RFID** (bastão Bluetooth), **QR code** no brinco ou OCR do brinco na imagem.

## Condições do Pantanal

- **Sol forte**: tela com alto contraste e modo "sol" no app; evitar captura ao meio-dia.
- **Poeira e barro**: o sistema precisa tolerar patas cobertas (os keypoints de casco têm confiança menor).
- **Bateria**: powerbank para o celular; estação em nobreak ou gerador.
- **Animais ariscos**: priorizar a captura no **tronco ou corredor**, não solto no pasto.
