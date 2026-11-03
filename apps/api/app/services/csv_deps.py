"""Parser de CSV para importacao de DEPs (PMGZ, ANCP, Geneplus).

O CSV tem colunas variaveis entre programas. A funcao aceita um mapeamento
de colunas e e flexivel quanto a nomes (case-insensitive).

Colunas de identificacao (ao menos uma obrigatoria):
    brinco, rgn ou rgd

Colunas DEP (case-insensitive, todas opcionais):
    P120, P210, P365, P450, PE, IPP, STAY, PP30, AOL, ACAB, MP120

Colunas meta (opcionais):
    programa, safra, indice (ou dti) — indice do programa, deca
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date
from typing import Any

_DEP_COLS = {
    "p120", "p210", "p365", "p450", "pe", "ipp", "stay", "pp30", "aol", "acab", "mp120",
}


def _float_opt(v: str) -> float | None:
    v = v.strip()
    if not v:
        return None
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return None


def _int_opt(v: str) -> int | None:
    v = v.strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def parse_csv_deps(
    conteudo: str,
    fazenda_id: uuid.UUID,
    programa: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Parseia CSV de DEPs e retorna (linhas_validas, erros).

    Cada linha valida e um dict com os campos de DadosGeneticos.
    Cada erro e {"linha": str, "motivo": str}.
    """
    linhas: list[dict[str, Any]] = []
    erros: list[dict[str, str]] = []

    reader = csv.DictReader(io.StringIO(conteudo))
    if reader.fieldnames is None:
        erros.append({"linha": "cabecalho", "motivo": "arquivo vazio ou sem cabecalho"})
        return linhas, erros

    # Normaliza nomes de colunas (strip + lower)
    norm_fields: dict[str, str] = {
        c.strip().lower(): c for c in reader.fieldnames if c
    }

    id_cols = [c for c in ("brinco", "rgn", "rgd") if c in norm_fields]
    if not id_cols:
        erros.append({
            "linha": "cabecalho",
            "motivo": "CSV precisa de ao menos uma coluna de identificacao: brinco, rgn ou rgd",
        })
        return linhas, erros

    dep_cols_presentes = [c for c in _DEP_COLS if c in norm_fields]

    # Coluna de indice pode vir como 'indice', 'dti', 'indice_programa'
    indice_col: str | None = None
    for cand in ("indice_programa", "indice", "dti"):
        if cand in norm_fields:
            indice_col = cand
            break

    hoje = date.today()

    for i, row in enumerate(reader, start=2):
        row_norm = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
        try:
            # Identificacao
            identificador = None
            for col in id_cols:
                v = row_norm.get(col, "")
                if v:
                    identificador = v
                    break
            if not identificador:
                erros.append({
                    "linha": str(i),
                    "motivo": "nenhum identificador de animal preenchido",
                })
                continue

            # DEPs
            deps: dict[str, float] = {}
            for col in dep_cols_presentes:
                val = _float_opt(row_norm.get(col, ""))
                if val is not None:
                    deps[col.upper()] = val

            # Meta
            programa_linha = row_norm.get("programa", "") or programa
            safra = row_norm.get("safra") or None
            indice = _float_opt(row_norm.get(indice_col, "")) if indice_col else None
            deca = _int_opt(row_norm.get("deca", ""))

            linhas.append({
                "fazenda_id": fazenda_id,
                # identificadores para lookup do animal
                "brinco": row_norm.get("brinco") or None,
                "rgn": row_norm.get("rgn") or None,
                "rgd": row_norm.get("rgd") or None,
                # campos de DadosGeneticos
                "programa": programa_linha or None,
                "safra": safra,
                "deps": deps if deps else None,
                "indice_programa": indice,
                "deca": deca,
                "data_importacao": hoje,
            })
        except Exception as exc:
            erros.append({"linha": str(i), "motivo": str(exc)})

    return linhas, erros
