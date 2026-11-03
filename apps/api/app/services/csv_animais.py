"""Parser de CSV para importacao em massa de animais.

Formato esperado — colunas minimas:
    brinco (ou rgn), sexo

Colunas opcionais:
    rgn, rgd, nascimento (YYYY-MM-DD ou DD/MM/YYYY),
    raca (default Nelore), ceip (sim/nao/true/false),
    variedade (padrao/mocho), observacoes
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date, datetime
from typing import Any


def _bool_csv(v: str) -> bool:
    return v.strip().lower() in {"sim", "true", "1", "s", "yes"}


def _data_csv(v: str) -> date | None:
    v = v.strip()
    if not v:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"data invalida: {v!r} (use YYYY-MM-DD ou DD/MM/YYYY)")


def parse_csv_animais(
    conteudo: str,
    fazenda_id: uuid.UUID,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Parseia CSV e retorna (linhas_validas, erros).

    Cada linha valida e um dict pronto para Animal(**linha).
    Cada erro e {"linha": str, "motivo": str}.
    """
    linhas: list[dict[str, Any]] = []
    erros: list[dict[str, str]] = []

    reader = csv.DictReader(io.StringIO(conteudo))
    if reader.fieldnames is None:
        erros.append({"linha": "cabecalho", "motivo": "arquivo vazio ou sem cabecalho"})
        return linhas, erros

    campos = {c.strip().lower() for c in reader.fieldnames if c}
    if "brinco" not in campos and "rgn" not in campos:
        erros.append({
            "linha": "cabecalho",
            "motivo": "CSV precisa de pelo menos a coluna 'brinco' ou 'rgn'",
        })
        return linhas, erros
    if "sexo" not in campos:
        erros.append({"linha": "cabecalho", "motivo": "coluna 'sexo' obrigatoria"})
        return linhas, erros

    for i, row in enumerate(reader, start=2):
        row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
        try:
            sexo_raw = row.get("sexo", "").upper()
            if sexo_raw in {"M", "MACHO"}:
                sexo = "M"
            elif sexo_raw in {"F", "FEMEA", "FÊMEA"}:
                sexo = "F"
            else:
                raise ValueError(f"sexo invalido: {row.get('sexo')!r} (use M ou F)")

            nascimento = _data_csv(row.get("nascimento", ""))
            ceip = _bool_csv(row.get("ceip", ""))
            variedade = row.get("variedade", "").lower() or None
            if variedade and variedade not in {"padrao", "mocho"}:
                variedade = None

            linhas.append({
                "fazenda_id": fazenda_id,
                "brinco": row.get("brinco") or None,
                "rgn": row.get("rgn") or None,
                "rgd": row.get("rgd") or None,
                "sexo": sexo,
                "nascimento": nascimento,
                "raca": row.get("raca") or "Nelore",
                "ceip": ceip,
                "variedade": variedade,
                "observacoes": row.get("observacoes") or None,
            })
        except ValueError as exc:
            erros.append({"linha": str(i), "motivo": str(exc)})

    return linhas, erros
