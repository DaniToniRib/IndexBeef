"""Projecao de peso futuro (ver docs/05-avaliacoes-e-indices.md, secao 2).

MVP: **curva de crescimento de Brody** para Nelore, com parametros por sexo
vindos de config/indices.yaml:

    W(t) = A * (1 - B * exp(-k * t))     [t em meses, W em kg]

Fluxo:
1. Carrega A, B, k do config (`projecao.brody.<sexo>`) — ou passa parametros
   explicitamente nos testes.
2. **Ajusta A** para que a curva passe pelo (peso_atual, idade_atual). Isso e
   um fit de 1 ponto — mantemos B e k da literatura, so recalibramos o peso
   assintotico ao individuo (crude mas util para a Fase 0, dado que nao temos
   dataset proprio ainda).
3. Avalia a curva ajustada em `idades_alvo_meses` (default [18, 24, 30]).
4. Devolve uma faixa min/max por `faixa_pct` em torno de cada ponto.

Entradas opcionais (Frame score, GMD historico, DEPs P210/P365/P450) estao
previstas no docs/05 §2 e entrarao na Fase 1+ junto com modelo treinado.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

Sexo = Literal["femea", "macho"]
IDADES_ALVO_PADRAO: tuple[int, ...] = (18, 24, 30)
FAIXA_PCT_PADRAO: float = 0.08


@dataclass(frozen=True)
class ParametrosBrody:
    """Parametros da curva W(t) = A * (1 - B * exp(-k*t))."""

    peso_adulto_kg: float  # A
    B: float
    k: float


# Parametros fallback caso o config nao esteja disponivel.
# Mesmos valores do config/indices.yaml (bloco projecao.brody).
PARAMETROS_PADRAO: dict[Sexo, ParametrosBrody] = {
    "femea": ParametrosBrody(peso_adulto_kg=450.0, B=0.90, k=0.045),
    "macho": ParametrosBrody(peso_adulto_kg=650.0, B=0.90, k=0.040),
}


@dataclass(frozen=True)
class PontoProjecao:
    idade_meses: int
    peso_kg: float
    peso_min_kg: float
    peso_max_kg: float


@dataclass(frozen=True)
class ProjecaoPeso:
    pontos: tuple[PontoProjecao, ...]
    parametros_ajustados: ParametrosBrody
    sexo: Sexo
    metodo: str = "brody_fit_1_ponto"


def peso_brody(t_meses: float, params: ParametrosBrody) -> float:
    """Avalia a curva de Brody. Retorna peso em kg."""
    if t_meses < 0:
        raise ValueError(f"idade precisa ser >= 0 (t_meses={t_meses})")
    return params.peso_adulto_kg * (1.0 - params.B * math.exp(-params.k * t_meses))


def ajustar_peso_adulto(
    peso_atual_kg: float, idade_atual_meses: float, params: ParametrosBrody,
) -> ParametrosBrody:
    """Reajusta A de modo que a curva passe por (peso_atual, idade_atual).

    Mantem B e k. Util quando nao ha dataset proprio ainda — individualiza
    somente o patamar adulto.
    """
    if peso_atual_kg <= 0 or idade_atual_meses <= 0:
        raise ValueError(
            f"peso_atual_kg e idade_atual_meses precisam ser > 0 "
            f"(peso={peso_atual_kg}, idade={idade_atual_meses})",
        )
    fator = 1.0 - params.B * math.exp(-params.k * idade_atual_meses)
    if fator <= 0:
        raise ValueError(
            "parametros Brody incompativeis: 1 - B*exp(-k*t) <= 0 "
            "(a curva nao esta definida nessa idade)",
        )
    novo_A = peso_atual_kg / fator
    return ParametrosBrody(peso_adulto_kg=novo_A, B=params.B, k=params.k)


def projetar(
    peso_atual_kg: float,
    idade_atual_meses: float,
    sexo: Sexo,
    params: ParametrosBrody | None = None,
    idades_alvo_meses: tuple[int, ...] = IDADES_ALVO_PADRAO,
    faixa_pct: float = FAIXA_PCT_PADRAO,
) -> ProjecaoPeso:
    """Projeta peso futuro usando Brody ajustado ao individuo.

    Para idades alvo <= idade atual, usa a curva ajustada mesmo assim
    (interpolacao suave; pode ser util para suavizar reavaliacoes).
    """
    if sexo not in ("femea", "macho"):
        raise ValueError(f"sexo invalido: {sexo!r} (esperado 'femea' ou 'macho')")
    if faixa_pct < 0:
        raise ValueError(f"faixa_pct precisa ser >= 0 (faixa_pct={faixa_pct})")
    base = params if params is not None else PARAMETROS_PADRAO[sexo]
    ajustado = ajustar_peso_adulto(peso_atual_kg, idade_atual_meses, base)

    pontos: list[PontoProjecao] = []
    for t in idades_alvo_meses:
        peso = peso_brody(t, ajustado)
        pontos.append(
            PontoProjecao(
                idade_meses=t,
                peso_kg=peso,
                peso_min_kg=peso * (1.0 - faixa_pct),
                peso_max_kg=peso * (1.0 + faixa_pct),
            ),
        )
    return ProjecaoPeso(
        pontos=tuple(pontos),
        parametros_ajustados=ajustado,
        sexo=sexo,
    )


def carregar_parametros_do_yaml(caminho: Path, sexo: Sexo) -> ParametrosBrody:
    """Le `projecao.brody.<sexo>` de um arquivo YAML (config/indices.yaml)."""
    data = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    try:
        bloco = data["projecao"]["brody"][sexo]
        return ParametrosBrody(
            peso_adulto_kg=float(bloco["peso_adulto_kg"]),
            B=float(bloco["B"]),
            k=float(bloco["k"]),
        )
    except (KeyError, TypeError) as e:
        raise ValueError(
            f"YAML sem chave projecao.brody.{sexo}.*: {caminho}",
        ) from e


def carregar_faixa_pct(caminho: Path) -> float:
    """Le `projecao.faixa_pct` do YAML (default se ausente)."""
    data = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    try:
        return float(data["projecao"]["faixa_pct"])
    except (KeyError, TypeError):
        return FAIXA_PCT_PADRAO
