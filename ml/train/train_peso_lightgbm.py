#!/usr/bin/env python
"""Treina o modelo LightGBM de estimativa de peso.

Uso:
    python ml/train/train_peso_lightgbm.py \\
        --db postgresql://indexbeef:indexbeef@localhost/indexbeef \\
        --saida ml/train/peso_model.json \\
        --safra pantanal_2026
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# LightGBM e dependencias ML (nao instaladas no venv da API — apenas ML)
try:
    import lightgbm as lgb
    import numpy as np
    from sklearn.model_selection import KFold
    from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score

    _ML_DISPONIVEL = True
except ImportError as _e:
    _ML_DISPONIVEL = False
    _IMPORT_ERROR = str(_e)


FEATURES = [
    "altura_cernelha_cm",
    "altura_garupa_cm",
    "comprimento_corporal_cm",
    "profundidade_toracica_cm",
    "comprimento_garupa_cm",
    "largura_garupa_cm",
    "altura_cupim_cm",
    "umbigo_chao_cm",
    "perimetro_toracico_est_cm",
    "sexo_num",        # 0=femea, 1=macho (derivado de sexo em parametros_entrada)
    "idade_meses",     # de parametros_entrada
]

TARGET = "peso_kg"


def _conectar(url: str):
    """Retorna engine SQLAlchemy."""
    try:
        from sqlalchemy import create_engine
    except ImportError:
        print("sqlalchemy nao instalado. Execute: pip install sqlalchemy psycopg2-binary")
        sys.exit(1)
    return create_engine(url, future=True)


def _carregar_dados(engine) -> tuple[list[dict[str, Any]], list[float]]:
    """Consulta o banco e retorna (X_rows, y_list).

    JOIN: avaliacao + medida_avaliacao + animal + pesagem
    Pesagem deve ser da balanca (origem='balanca') na mesma data que a avaliacao.
    """
    from sqlalchemy import text

    query = text("""
        SELECT
            ma.altura_cernelha_cm,
            ma.altura_garupa_cm,
            ma.comprimento_corporal_cm,
            ma.profundidade_toracica_cm,
            ma.comprimento_garupa_cm,
            ma.largura_garupa_cm,
            ma.altura_cupim_cm,
            ma.umbigo_chao_cm,
            ma.perimetro_toracico_est_cm,
            av.parametros_entrada,
            p.peso_kg
        FROM avaliacao av
        JOIN medida_avaliacao ma ON ma.avaliacao_id = av.id
        JOIN animal a ON a.id = av.animal_id
        JOIN pesagem p ON p.animal_id = av.animal_id
            AND p.origem = 'balanca'
            AND p.data BETWEEN (av.data_hora::date - INTERVAL '1 day')
                         AND (av.data_hora::date + INTERVAL '1 day')
        WHERE ma.altura_cernelha_cm IS NOT NULL
          AND p.peso_kg IS NOT NULL
    """)

    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    X_rows: list[dict[str, Any]] = []
    y: list[float] = []

    for row in rows:
        params = row.parametros_entrada or {}
        sexo_str = params.get("sexo", "femea")
        sexo_num = 1 if sexo_str == "macho" else 0
        idade_meses = float(params.get("idade_meses", 24))

        feat: dict[str, Any] = {
            "altura_cernelha_cm": float(row.altura_cernelha_cm or 0),
            "altura_garupa_cm": float(row.altura_garupa_cm or 0),
            "comprimento_corporal_cm": float(row.comprimento_corporal_cm or 0),
            "profundidade_toracica_cm": float(row.profundidade_toracica_cm or 0),
            "comprimento_garupa_cm": float(row.comprimento_garupa_cm or 0),
            "largura_garupa_cm": float(row.largura_garupa_cm or 0),
            "altura_cupim_cm": float(row.altura_cupim_cm or 0),
            "umbigo_chao_cm": float(row.umbigo_chao_cm or 0),
            "perimetro_toracico_est_cm": float(row.perimetro_toracico_est_cm or 0),
            "sexo_num": sexo_num,
            "idade_meses": idade_meses,
        }
        X_rows.append(feat)
        y.append(float(row.peso_kg))

    return X_rows, y


def _treinar(X_rows: list[dict], y: list[float], n_folds: int = 5) -> tuple[Any, dict]:
    """Treina LightGBM com validacao cruzada e retorna (modelo_final, metricas)."""
    X = np.array([[row[f] for f in FEATURES] for row in X_rows])
    y_arr = np.array(y)

    params_lgb = {
        "objective": "regression",
        "metric": "mape",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "n_estimators": 300,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_samples": 5,
        "random_state": 42,
        "verbose": -1,
    }

    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    mapes: list[float] = []
    maes: list[float] = []
    r2s: list[float] = []

    for fold, (idx_train, idx_val) in enumerate(kf.split(X), 1):
        X_tr, X_val = X[idx_train], X[idx_val]
        y_tr, y_val = y_arr[idx_train], y_arr[idx_val]

        modelo = lgb.LGBMRegressor(**params_lgb)
        modelo.fit(X_tr, y_tr)
        y_pred = modelo.predict(X_val)

        mapes.append(float(mean_absolute_percentage_error(y_val, y_pred) * 100))
        maes.append(float(mean_absolute_error(y_val, y_pred)))
        r2s.append(float(r2_score(y_val, y_pred)))
        print(f"  Fold {fold}: MAPE={mapes[-1]:.2f}%  MAE={maes[-1]:.1f}kg  R²={r2s[-1]:.4f}")

    metricas = {
        "mape_pct_cv_mean": round(float(np.mean(mapes)), 3),
        "mape_pct_cv_std": round(float(np.std(mapes)), 3),
        "mae_kg_cv_mean": round(float(np.mean(maes)), 3),
        "r2_cv_mean": round(float(np.mean(r2s)), 4),
        "n_amostras": len(y),
        "features": FEATURES,
    }

    # Treinar modelo final com todos os dados
    modelo_final = lgb.LGBMRegressor(**params_lgb)
    modelo_final.fit(X, y_arr)

    return modelo_final, metricas


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina modelo LightGBM de estimativa de peso")
    parser.add_argument(
        "--db",
        default=os.getenv("DATABASE_URL", "postgresql://indexbeef:indexbeef@localhost/indexbeef"),
        help="URL do banco de dados (SQLAlchemy)",
    )
    parser.add_argument(
        "--saida",
        default="ml/train/peso_model.json",
        help="Arquivo de saida para o modelo (.json)",
    )
    parser.add_argument(
        "--safra",
        default=None,
        help="Identificador da safra (usado nos metadados)",
    )
    parser.add_argument(
        "--folds",
        type=int,
        default=5,
        help="Numero de folds para validacao cruzada",
    )
    args = parser.parse_args()

    if not _ML_DISPONIVEL:
        print(f"Erro: dependencias ML nao encontradas ({_IMPORT_ERROR})")
        print("Instale: pip install lightgbm scikit-learn numpy")
        sys.exit(1)

    print(f"Conectando ao banco: {args.db[:40]}...")
    engine = _conectar(args.db)

    print("Carregando dados...")
    X_rows, y = _carregar_dados(engine)
    print(f"  {len(y)} pares (avaliacao, pesagem) encontrados")

    if len(y) < 10:
        print("Dados insuficientes para treinar (minimo 10 amostras). Abortando.")
        sys.exit(1)

    print(f"Treinando com {args.folds}-fold CV...")
    modelo, metricas = _treinar(X_rows, y, n_folds=args.folds)

    if args.safra:
        metricas["safra"] = args.safra

    print("\nResultados:")
    print(f"  MAPE CV: {metricas['mape_pct_cv_mean']:.2f}% ± {metricas['mape_pct_cv_std']:.2f}%")
    print(f"  MAE CV:  {metricas['mae_kg_cv_mean']:.1f} kg")
    print(f"  R² CV:   {metricas['r2_cv_mean']:.4f}")

    # Salvar modelo
    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    modelo.booster_.save_model(str(saida))
    print(f"\nModelo salvo em: {saida}")

    # Salvar metricas
    saida_metricas = saida.with_suffix(".metricas.json")
    with open(saida_metricas, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
    print(f"Metricas salvas em: {saida_metricas}")

    print("\nPara registrar o modelo na API:")
    print(f"  POST /modelos-versao")
    print(f'  {{"nome": "peso", "versao": "0.1.0", "metricas": {json.dumps(metricas)[:80]}...}}')


if __name__ == "__main__":
    main()
