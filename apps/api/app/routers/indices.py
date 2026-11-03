"""Router de indices de aptidao — Frame score, EPMURAS, GMD, projecao de peso e ranking."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.animal import Animal
from app.models.avaliacao import Avaliacao
from app.models.caixa_virtual_avaliacao import CaixaVirtualAvaliacao
from app.models.dados_geneticos import DadosGeneticos
from app.models.enums import Sexo, TipoEventoReprodutivo
from app.models.escore_avaliacao import EscoreAvaliacao
from app.models.evento_reprodutivo import EventoReprodutivo
from app.models.exame_andrologico import ExameAndrologico
from app.models.lote import Lote
from app.models.medida_avaliacao import MedidaAvaliacao
from app.models.pesagem import Pesagem
from app.models.predicao_avaliacao import PredicaoAvaliacao
from app.schemas.avaliacao import (
    GmdResponse,
    IndiceItemResponse,
    IndiceResultadoResponse,
    MatrizPrenheResponse,
    ProjecaoPesoResponse,
    RankingItemResponse,
    RankingResponse,
)
from app.services.indices_service import (
    _cfg,
    calcular_frame_score,
    calcular_gmd,
    calcular_indice,
    calcular_projecao_brody,
    montar_componentes_garrote,
    montar_componentes_matriz,
    montar_componentes_reprodutor,
    sugerir_epmuras,
)

router = APIRouter(tags=["indices"])


def _medidas_dict(m: MedidaAvaliacao | None) -> dict:
    if m is None:
        return {}
    return {
        "altura_cernelha_cm": float(m.altura_cernelha_cm) if m.altura_cernelha_cm else None,
        "altura_garupa_cm": float(m.altura_garupa_cm) if m.altura_garupa_cm else None,
        "comprimento_corporal_cm": float(m.comprimento_corporal_cm) if m.comprimento_corporal_cm else None,
        "profundidade_toracica_cm": float(m.profundidade_toracica_cm) if m.profundidade_toracica_cm else None,
        "comprimento_garupa_cm": float(m.comprimento_garupa_cm) if m.comprimento_garupa_cm else None,
        "largura_garupa_cm": float(m.largura_garupa_cm) if m.largura_garupa_cm else None,
        "umbigo_chao_cm": float(m.umbigo_chao_cm) if m.umbigo_chao_cm else None,
        "inclinacao_garupa_graus": float(m.inclinacao_garupa_graus) if m.inclinacao_garupa_graus else None,
    }


def _caixa_dict(c: CaixaVirtualAvaliacao | None) -> dict:
    if c is None:
        return {}
    return {
        "volume_l": float(c.volume_l) if c.volume_l else None,
        "ipl": float(c.ipl) if c.ipl else None,
        "compacidade": float(c.compacidade) if c.compacidade else None,
        "indice_comprimento": float(c.indice_comprimento) if c.indice_comprimento else None,
    }


def _escore_dict(e: EscoreAvaliacao | None) -> dict:
    if e is None:
        return {}
    return {
        "ecc_sugerido": float(e.ecc_sugerido) if e.ecc_sugerido else None,
        "ecc_final": float(e.ecc_final) if e.ecc_final else None,
        "e_sugerido": e.e_sugerido,
        "e_final": e.e_final,
        "p_sugerido": e.p_sugerido,
        "p_final": e.p_final,
        "m_sugerido": e.m_sugerido,
        "m_final": e.m_final,
        "u_sugerido": e.u_sugerido,
        "u_final": e.u_final,
        "r_sugerido": e.r_sugerido,
        "r_final": e.r_final,
        "a_sugerido": e.a_sugerido,
        "a_final": e.a_final,
        "s_sugerido": e.s_sugerido,
        "s_final": e.s_final,
    }


@router.post(
    "/indices/avaliacoes/{avaliacao_id}/calcular",
    response_model=IndiceResultadoResponse,
    status_code=status.HTTP_201_CREATED,
)
def calcular_indices_avaliacao(
    avaliacao_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> IndiceResultadoResponse:
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status_code=404, detail="avaliacao nao encontrada")

    animal = db.get(Animal, avaliacao.animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="animal nao encontrado")

    medida = db.scalars(
        select(MedidaAvaliacao).where(MedidaAvaliacao.avaliacao_id == avaliacao_id),
    ).first()
    caixa = db.scalars(
        select(CaixaVirtualAvaliacao).where(CaixaVirtualAvaliacao.avaliacao_id == avaliacao_id),
    ).first()
    escore = db.scalars(
        select(EscoreAvaliacao).where(EscoreAvaliacao.avaliacao_id == avaliacao_id),
    ).first()

    pesagens_db = list(db.scalars(
        select(Pesagem)
        .where(Pesagem.animal_id == animal.id)
        .order_by(Pesagem.data),
    ).all())
    pesagens = [{"data": p.data, "peso_kg": float(p.peso_kg)} for p in pesagens_db]

    dados_gen = db.scalars(
        select(DadosGeneticos).where(DadosGeneticos.animal_id == animal.id),
    ).first()

    exame_and = db.scalars(
        select(ExameAndrologico)
        .where(ExameAndrologico.animal_id == animal.id)
        .order_by(ExameAndrologico.data.desc()),
    ).first()

    medidas_d = _medidas_dict(medida)
    caixa_d = _caixa_dict(caixa)
    escore_d = _escore_dict(escore)
    deps = dados_gen.deps if dados_gen else None
    exame_d = {
        "perimetro_escrotal_cm": float(exame_and.perimetro_escrotal_cm) if exame_and and exame_and.perimetro_escrotal_cm else None,
    } if exame_and else None

    cfg = _cfg()

    frame_score: float | None = None
    if medidas_d.get("altura_garupa_cm") and animal.nascimento:
        data_aval = avaliacao.data_hora.date() if hasattr(avaliacao.data_hora, "date") else avaliacao.data_hora
        frame_score = calcular_frame_score(
            medidas_d["altura_garupa_cm"],
            animal.sexo.value,
            animal.nascimento,
            data_aval,
        )

    if frame_score is not None:
        if escore is None:
            escore = EscoreAvaliacao(avaliacao_id=avaliacao_id, frame_score=frame_score)
            db.add(escore)
        else:
            escore.frame_score = frame_score
        escore_d["frame_score"] = frame_score

    epmuras_sugerido = sugerir_epmuras(medidas_d, caixa_d)

    if escore is not None:
        for letra, campo in [("E", "e"), ("P", "p"), ("M", "m"), ("U", "u")]:
            valor = epmuras_sugerido.get(letra)
            if valor is not None and getattr(escore, f"{campo}_sugerido") is None:
                setattr(escore, f"{campo}_sugerido", valor)
                escore_d[f"{campo}_sugerido"] = valor

    gmd = calcular_gmd(pesagens)

    data_aval_dt = avaliacao.data_hora.date() if hasattr(avaliacao.data_hora, "date") else avaliacao.data_hora

    peso_atual: float | None = None
    if pesagens:
        peso_atual = pesagens[-1]["peso_kg"]
    else:
        peso_pred = db.scalars(
            select(PredicaoAvaliacao)
            .where(
                PredicaoAvaliacao.avaliacao_id == avaliacao_id,
                PredicaoAvaliacao.tipo == "peso_atual",
            ),
        ).first()
        if peso_pred and peso_pred.valor:
            peso_atual = float(peso_pred.valor)

    idade_atual_meses: float | None = None
    if animal.nascimento:
        idade_atual_meses = (data_aval_dt - animal.nascimento).days / 30.44

    if peso_atual and idade_atual_meses:
        db.execute(
            delete(PredicaoAvaliacao).where(
                PredicaoAvaliacao.avaliacao_id == avaliacao_id,
                PredicaoAvaliacao.tipo.like("peso_%m"),
            ),
        )
        projecoes = calcular_projecao_brody(peso_atual, animal.sexo.value, idade_atual_meses, frame_score, cfg)
        for pt in projecoes:
            db.add(PredicaoAvaliacao(
                avaliacao_id=avaliacao_id,
                tipo=f"peso_{pt['idade_meses']}m",
                valor=pt["peso_kg"],
                faixa_min=pt["peso_min_kg"],
                faixa_max=pt["peso_max_kg"],
                metodo="brody",
            ))

    lote_id = animal.lote_id
    sexo_animal = animal.sexo.value

    def _grupo_valores(tipo_indice: str) -> list[float]:
        if lote_id is None:
            return []
        stmt = (
            select(PredicaoAvaliacao.valor)
            .join(Avaliacao, Avaliacao.id == PredicaoAvaliacao.avaliacao_id)
            .join(Animal, Animal.id == Avaliacao.animal_id)
            .where(
                Animal.lote_id == lote_id,
                Animal.sexo == sexo_animal,
                PredicaoAvaliacao.tipo == tipo_indice,
                PredicaoAvaliacao.valor.isnot(None),
            )
        )
        return [float(v) for v in db.scalars(stmt).all()]

    indices_calculados: list[IndiceItemResponse] = []

    componentes_garrote = montar_componentes_garrote(
        medidas_d, caixa_d, escore_d, gmd, deps, peso_atual, animal.nascimento, data_aval_dt,
    )
    grupo_garrote = _grupo_valores("indice_garrote")
    val_garrote, expl_garrote = calcular_indice("garrote", componentes_garrote, grupo_garrote, cfg)

    db.execute(
        delete(PredicaoAvaliacao).where(
            PredicaoAvaliacao.avaliacao_id == avaliacao_id,
            PredicaoAvaliacao.tipo == "indice_garrote",
        ),
    )
    db.add(PredicaoAvaliacao(
        avaliacao_id=avaliacao_id,
        tipo="indice_garrote",
        valor=val_garrote,
        explicacao=expl_garrote,
    ))
    indices_calculados.append(IndiceItemResponse(
        tipo="indice_garrote", valor=val_garrote, explicacao=expl_garrote,
    ))

    if sexo_animal == "M":
        componentes_rep = montar_componentes_reprodutor(medidas_d, caixa_d, escore_d, deps, exame_d)
        grupo_rep = _grupo_valores("indice_reprodutor")
        val_rep, expl_rep = calcular_indice("reprodutor", componentes_rep, grupo_rep, cfg)

        db.execute(
            delete(PredicaoAvaliacao).where(
                PredicaoAvaliacao.avaliacao_id == avaliacao_id,
                PredicaoAvaliacao.tipo == "indice_reprodutor",
            ),
        )
        db.add(PredicaoAvaliacao(
            avaliacao_id=avaliacao_id,
            tipo="indice_reprodutor",
            valor=val_rep,
            explicacao=expl_rep,
        ))
        indices_calculados.append(IndiceItemResponse(
            tipo="indice_reprodutor", valor=val_rep, explicacao=expl_rep,
        ))

    if sexo_animal == "F":
        componentes_mat = montar_componentes_matriz(medidas_d, caixa_d, escore_d, deps)
        grupo_mat = _grupo_valores("indice_matriz")
        val_mat, expl_mat = calcular_indice("matriz", componentes_mat, grupo_mat, cfg)

        db.execute(
            delete(PredicaoAvaliacao).where(
                PredicaoAvaliacao.avaliacao_id == avaliacao_id,
                PredicaoAvaliacao.tipo == "indice_matriz",
            ),
        )
        db.add(PredicaoAvaliacao(
            avaliacao_id=avaliacao_id,
            tipo="indice_matriz",
            valor=val_mat,
            explicacao=expl_mat,
        ))
        indices_calculados.append(IndiceItemResponse(
            tipo="indice_matriz", valor=val_mat, explicacao=expl_mat,
        ))

    db.commit()

    return IndiceResultadoResponse(
        avaliacao_id=str(avaliacao_id),
        frame_score=frame_score,
        epmuras_sugerido=epmuras_sugerido,
        gmd_kg_dia=gmd,
        indices=indices_calculados,
    )


@router.get("/lotes/{lote_id}/ranking", response_model=RankingResponse)
def ranking_lote(
    lote_id: uuid.UUID,
    indice: str = Query(default="garrote"),
    db: Session = Depends(get_db),
) -> RankingResponse:
    lote = db.get(Lote, lote_id)
    if lote is None:
        raise HTTPException(status_code=404, detail="lote nao encontrado")

    tipo_indice = f"indice_{indice}"

    stmt = (
        select(Animal.id, Animal.brinco, PredicaoAvaliacao.valor)
        .join(Avaliacao, Avaliacao.animal_id == Animal.id)
        .join(PredicaoAvaliacao, PredicaoAvaliacao.avaliacao_id == Avaliacao.id)
        .where(
            Animal.lote_id == lote_id,
            PredicaoAvaliacao.tipo == tipo_indice,
            PredicaoAvaliacao.valor.isnot(None),
        )
        .order_by(Avaliacao.data_hora.desc())
    )

    rows = db.execute(stmt).all()

    seen: dict[str, tuple] = {}
    for row in rows:
        animal_id_str = str(row[0])
        if animal_id_str not in seen:
            seen[animal_id_str] = (row[1], float(row[2]))

    ordenados = sorted(seen.items(), key=lambda x: x[1][1], reverse=True)

    itens = [
        RankingItemResponse(
            animal_id=aid,
            brinco=brinco_val,
            nome=None,
            valor=valor_f,
            posicao=pos + 1,
            confianca=None,
        )
        for pos, (aid, (brinco_val, valor_f)) in enumerate(ordenados)
    ]

    return RankingResponse(total=len(itens), itens=itens)


@router.get("/lotes/{lote_id}/matrizes-prenhes", response_model=list[MatrizPrenheResponse])
def matrizes_prenhes(
    lote_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> list[MatrizPrenheResponse]:
    lote = db.get(Lote, lote_id)
    if lote is None:
        raise HTTPException(status_code=404, detail="lote nao encontrado")

    femeas = list(db.scalars(
        select(Animal).where(
            Animal.lote_id == lote_id,
            Animal.sexo == Sexo.F,
        ),
    ).all())

    resultado = []
    for animal in femeas:
        eventos = list(db.scalars(
            select(EventoReprodutivo)
            .where(EventoReprodutivo.animal_id == animal.id)
            .order_by(EventoReprodutivo.data.desc()),
        ).all())

        if not eventos:
            continue

        ultimo = eventos[0]
        if ultimo.tipo != TipoEventoReprodutivo.diagnostico_gestacao:
            continue

        data_diag = ultimo.data

        escore_rec = db.scalars(
            select(EscoreAvaliacao)
            .join(Avaliacao, Avaliacao.id == EscoreAvaliacao.avaliacao_id)
            .where(Avaliacao.animal_id == animal.id)
            .order_by(Avaliacao.data_hora.desc()),
        ).first()

        ecc_atual: float | None = None
        if escore_rec and escore_rec.ecc_final:
            ecc_atual = float(escore_rec.ecc_final)
        elif escore_rec and escore_rec.ecc_sugerido:
            ecc_atual = float(escore_rec.ecc_sugerido)

        alerta = ecc_atual is not None and (ecc_atual < 4.0 or ecc_atual > 8.0)

        resultado.append(MatrizPrenheResponse(
            animal_id=str(animal.id),
            brinco=animal.brinco,
            data_diagnostico=data_diag,
            ecc_atual=ecc_atual,
            alerta_ecc=alerta,
        ))

    return resultado


@router.get("/animais/{animal_id}/gmd", response_model=GmdResponse)
def gmd_animal(
    animal_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> GmdResponse:
    animal = db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="animal nao encontrado")

    pesagens_db = list(db.scalars(
        select(Pesagem)
        .where(Pesagem.animal_id == animal_id)
        .order_by(Pesagem.data),
    ).all())

    pesagens = [
        {"data": p.data, "peso_kg": float(p.peso_kg), "origem": p.origem.value}
        for p in pesagens_db
    ]

    from app.services.indices_service import calcular_gmd as _calc_gmd
    gmd = _calc_gmd(pesagens)

    return GmdResponse(gmd_kg_dia=gmd, pesagens=pesagens)


@router.get("/animais/{animal_id}/projecao-peso", response_model=ProjecaoPesoResponse)
def projecao_peso_animal(
    animal_id: uuid.UUID,
    avaliacao_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ProjecaoPesoResponse:
    animal = db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="animal nao encontrado")

    cfg = _cfg()
    frame_score: float | None = None
    peso_atual: float | None = None
    data_ref: date | None = None

    if avaliacao_id is not None:
        avaliacao = db.get(Avaliacao, avaliacao_id)
        if avaliacao:
            data_ref = avaliacao.data_hora.date() if hasattr(avaliacao.data_hora, "date") else avaliacao.data_hora
            escore = db.scalars(
                select(EscoreAvaliacao).where(EscoreAvaliacao.avaliacao_id == avaliacao_id),
            ).first()
            if escore and escore.frame_score:
                frame_score = float(escore.frame_score)
            peso_pred = db.scalars(
                select(PredicaoAvaliacao).where(
                    PredicaoAvaliacao.avaliacao_id == avaliacao_id,
                    PredicaoAvaliacao.tipo == "peso_atual",
                ),
            ).first()
            if peso_pred and peso_pred.valor:
                peso_atual = float(peso_pred.valor)

    if peso_atual is None:
        ultima_pesagem = db.scalars(
            select(Pesagem)
            .where(Pesagem.animal_id == animal_id)
            .order_by(Pesagem.data.desc()),
        ).first()
        if ultima_pesagem:
            peso_atual = float(ultima_pesagem.peso_kg)
            data_ref = ultima_pesagem.data

    if frame_score is None:
        ultima_aval = db.scalars(
            select(Avaliacao)
            .where(Avaliacao.animal_id == animal_id)
            .order_by(Avaliacao.data_hora.desc()),
        ).first()
        if ultima_aval:
            escore = db.scalars(
                select(EscoreAvaliacao).where(EscoreAvaliacao.avaliacao_id == ultima_aval.id),
            ).first()
            if escore and escore.frame_score:
                frame_score = float(escore.frame_score)

    idade_atual_meses: float | None = None
    if animal.nascimento and data_ref:
        idade_atual_meses = (data_ref - animal.nascimento).days / 30.44

    projecoes: list[dict] = []
    if peso_atual and idade_atual_meses:
        projecoes = calcular_projecao_brody(
            peso_atual, animal.sexo.value, idade_atual_meses, frame_score, cfg,
        )

    return ProjecaoPesoResponse(
        peso_atual_kg=peso_atual,
        idade_meses=idade_atual_meses,
        frame_score=frame_score,
        projecoes=projecoes,
    )
