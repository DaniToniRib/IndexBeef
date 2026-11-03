# Treinamento dos modelos IndexBeef

## Fluxo

1. Exportar keypoints (COCO): `python exportar_coco_cli.py --fazenda-id <UUID>`
2. Importar no CVAT:
   - Create task → Upload annotation → COCO 1.0
   - Revise e corrija os keypoints no CVAT
   - Exporte no formato COCO Keypoints
3. Treinar YOLO-pose: `yolo pose train data=indexbeef_pose.yaml model=yolov8n-pose.pt epochs=100`
4. Treinar LightGBM: `python train_peso_lightgbm.py --db <DATABASE_URL>`
5. Registrar modelos: `POST /modelos-versao`

## Scripts

| Script | Descricao |
|---|---|
| `exportar_coco_cli.py` | Exporta keypoints da API no formato COCO para anotacao |
| `train_peso_lightgbm.py` | Treina modelo de estimativa de peso com LightGBM |

## Dependencias (apenas para ML, nao para a API)

```bash
pip install lightgbm scikit-learn numpy requests
```

## Exemplo completo

```bash
# 1. Exportar keypoints de uma fazenda
python ml/train/exportar_coco_cli.py \
    --api http://localhost:8000 \
    --fazenda-id 00000000-0000-0000-0000-000000000001 \
    --saida ml/datasets/keypoints_coco.json

# 2. Apos anotar no CVAT, treinar YOLO-pose
yolo pose train \
    data=ml/datasets/indexbeef_pose.yaml \
    model=yolov8n-pose.pt \
    epochs=100 \
    imgsz=1280

# 3. Treinar modelo de peso
python ml/train/train_peso_lightgbm.py \
    --db postgresql://indexbeef:indexbeef@localhost/indexbeef \
    --saida ml/train/peso_model.json \
    --safra pantanal_2026

# 4. Registrar modelo treinado na API
curl -X POST http://localhost:8000/modelos-versao \
    -H "Content-Type: application/json" \
    -d '{
        "nome": "peso",
        "versao": "0.1.0",
        "metricas": {"mape_pct": 4.8, "mae_kg": 18.2},
        "artefato_url": "s3://indexbeef/models/peso_v0.1.0.json",
        "ativo": true
    }'
```

## Aguardando dataset (Fase 2)

Os modelos abaixo aguardam a coleta de campo:

- Fine-tuning da segmentacao para Nelore
- Modelo de keypoints lateral (YOLO-pose)
- Modelo de peso (LightGBM com dados reais)
