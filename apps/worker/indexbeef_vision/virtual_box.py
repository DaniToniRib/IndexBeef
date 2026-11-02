"""Caixa virtual + indices derivados (ver docs/04-pipeline-visao.md, secao 10).

- **Caixa** = C x P x L (cm3), equivalente a um volume aparente.
- **IPL** = area da silhueta do tronco / (C x P). Quanto mais proximo de 1,
  mais "cheio" e o animal (costela arqueada, flanco cheio).
- **Compacidade** = PT / AC. Animais profundos em relacao a altura tendem a
  ser mais precoces.
- **Indice de comprimento** = CC / AC. Indica espaco para carcaca.
"""

from __future__ import annotations

from dataclasses import dataclass

from indexbeef_vision.measurements import MedidasLineares


@dataclass(frozen=True)
class CaixaVirtual:
    c_cm: float
    p_cm: float
    l_cm: float | None
    volume_cm3: float | None
    volume_l: float | None
    ipl: float | None
    compacidade: float
    indice_comprimento: float


def montar_caixa_virtual(medidas: MedidasLineares) -> CaixaVirtual:
    """Monta a caixa virtual a partir das medidas.

    - `l_cm` depende de `MedidasLineares.largura_garupa` (vista traseira).
    - `volume_cm3` e `volume_l` so existem se `l_cm` existir.
    - `ipl` so existe se `MedidasLineares.area_tronco_cm2` existir.
    """
    c = medidas.comprimento_corporal
    p = medidas.profundidade_toracica
    ac = medidas.altura_cernelha
    l = medidas.largura_garupa

    volume_cm3 = c * p * l if l is not None else None
    volume_l = volume_cm3 / 1000.0 if volume_cm3 is not None else None

    ipl = (
        medidas.area_tronco_cm2 / (c * p)
        if medidas.area_tronco_cm2 is not None and (c * p) > 0
        else None
    )

    compacidade = p / ac if ac > 0 else 0.0
    indice_comprimento = c / ac if ac > 0 else 0.0

    return CaixaVirtual(
        c_cm=c,
        p_cm=p,
        l_cm=l,
        volume_cm3=volume_cm3,
        volume_l=volume_l,
        ipl=ipl,
        compacidade=compacidade,
        indice_comprimento=indice_comprimento,
    )
