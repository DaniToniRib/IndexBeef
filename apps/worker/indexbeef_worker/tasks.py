"""Tasks RQ do worker IndexBeef.

processar_avaliacao: le parametros_entrada da avaliacao, executa o pipeline
de visao e salva resultado + tabelas estruturadas via SQL direto (o worker
nao importa do pacote app/ da API — usa SQLAlchemy Core puro).
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

from sqlalchemy import create_engine, text

from indexbeef_vision.pipeline import VERSAO_PIPELINE, montar_payload


def _db_engine():
    url = (
        f"postgresql+psycopg://{os.getenv('POSTGRES_USER', 'indexbeef')}"
        f":{os.getenv('POSTGRES_PASSWORD', 'indexbeef')}"
        f"@{os.getenv('POSTGRES_HOST', 'db')}"
        f":{os.getenv('POSTGRES_PORT', '5432')}"
        f"/{os.getenv('POSTGRES_DB', 'indexbeef')}"
    )
    return create_engine(url, pool_pre_ping=True)


def _novo_id() -> str:
    return str(uuid.uuid4())


def _salvar_estruturado(conn, avaliacao_id: str, resultado: dict[str, Any]) -> None:
    mc = resultado.get("medidas_cm", {})
    ang = resultado.get("angulos_graus", {})

    def mv(nome: str):
        d = mc.get(nome)
        return d["valor"] if isinstance(d, dict) else None

    def mc_(nome: str):
        d = mc.get(nome)
        return d["confianca"] if isinstance(d, dict) else None

    conn.execute(text("""
        INSERT INTO medida_avaliacao (
            id, criado_em, atualizado_em, avaliacao_id,
            altura_cernelha_cm, altura_cernelha_conf,
            altura_garupa_cm, altura_garupa_conf,
            comprimento_corporal_cm, comprimento_corporal_conf,
            profundidade_toracica_cm, profundidade_toracica_conf,
            comprimento_garupa_cm, comprimento_garupa_conf,
            largura_garupa_cm, largura_garupa_conf,
            altura_cupim_cm, altura_cupim_conf,
            umbigo_chao_cm, umbigo_chao_conf,
            perimetro_toracico_est_cm, perimetro_toracico_est_conf,
            inclinacao_garupa_graus, jarrete_graus
        ) VALUES (
            :id, now(), now(), :avaliacao_id,
            :ac, :ac_c, :ag, :ag_c, :cc, :cc_c, :pt, :pt_c,
            :cg, :cg_c, :lg, :lg_c, :cup, :cup_c, :umb, :umb_c,
            :pte, :pte_c, :inc, :jar
        )
        ON CONFLICT (avaliacao_id) DO UPDATE SET
            atualizado_em = now(),
            altura_cernelha_cm = EXCLUDED.altura_cernelha_cm,
            altura_cernelha_conf = EXCLUDED.altura_cernelha_conf,
            altura_garupa_cm = EXCLUDED.altura_garupa_cm,
            comprimento_corporal_cm = EXCLUDED.comprimento_corporal_cm,
            profundidade_toracica_cm = EXCLUDED.profundidade_toracica_cm,
            comprimento_garupa_cm = EXCLUDED.comprimento_garupa_cm,
            largura_garupa_cm = EXCLUDED.largura_garupa_cm,
            altura_cupim_cm = EXCLUDED.altura_cupim_cm,
            umbigo_chao_cm = EXCLUDED.umbigo_chao_cm,
            perimetro_toracico_est_cm = EXCLUDED.perimetro_toracico_est_cm,
            inclinacao_garupa_graus = EXCLUDED.inclinacao_garupa_graus,
            jarrete_graus = EXCLUDED.jarrete_graus
    """), {
        "id": _novo_id(), "avaliacao_id": avaliacao_id,
        "ac": mv("altura_cernelha"), "ac_c": mc_("altura_cernelha"),
        "ag": mv("altura_garupa"), "ag_c": mc_("altura_garupa"),
        "cc": mv("comprimento_corporal"), "cc_c": mc_("comprimento_corporal"),
        "pt": mv("profundidade_toracica"), "pt_c": mc_("profundidade_toracica"),
        "cg": mv("comprimento_garupa"), "cg_c": mc_("comprimento_garupa"),
        "lg": mv("largura_garupa"), "lg_c": mc_("largura_garupa"),
        "cup": mv("altura_cupim"), "cup_c": mc_("altura_cupim"),
        "umb": mv("umbigo_chao"), "umb_c": mc_("umbigo_chao"),
        "pte": mv("perimetro_toracico_est"), "pte_c": mc_("perimetro_toracico_est"),
        "inc": ang.get("inclinacao_garupa"), "jar": ang.get("jarrete"),
    })

    cv = resultado.get("caixa_virtual", {})
    conn.execute(text("""
        INSERT INTO caixa_virtual_avaliacao (
            id, criado_em, atualizado_em, avaliacao_id,
            c_cm, p_cm, l_cm, volume_cm3, volume_l, ipl, compacidade, indice_comprimento
        ) VALUES (
            :id, now(), now(), :avaliacao_id,
            :c, :p, :l, :vcm3, :vl, :ipl, :comp, :ic
        )
        ON CONFLICT (avaliacao_id) DO UPDATE SET
            atualizado_em = now(),
            c_cm = EXCLUDED.c_cm, p_cm = EXCLUDED.p_cm, l_cm = EXCLUDED.l_cm,
            volume_l = EXCLUDED.volume_l, ipl = EXCLUDED.ipl,
            compacidade = EXCLUDED.compacidade, indice_comprimento = EXCLUDED.indice_comprimento
    """), {
        "id": _novo_id(), "avaliacao_id": avaliacao_id,
        "c": cv.get("C"), "p": cv.get("P"), "l": cv.get("L"),
        "vcm3": cv.get("volume_cm3"), "vl": cv.get("volume_l"),
        "ipl": cv.get("ipl"), "comp": cv.get("compacidade"),
        "ic": cv.get("indice_comprimento"),
    })

    conn.execute(
        text("DELETE FROM predicao_avaliacao WHERE avaliacao_id = :aid"),
        {"aid": avaliacao_id},
    )
    peso = resultado.get("peso", {})
    if peso.get("peso_kg") is not None:
        conn.execute(text("""
            INSERT INTO predicao_avaliacao
                (id, criado_em, atualizado_em, avaliacao_id, tipo, valor, metodo)
            VALUES (:id, now(), now(), :aid, 'peso_atual', :val, :met)
        """), {
            "id": _novo_id(), "aid": avaliacao_id,
            "val": peso["peso_kg"], "met": peso.get("metodo"),
        })

    for pt in resultado.get("projecao_peso", {}).get("pontos", []):
        conn.execute(text("""
            INSERT INTO predicao_avaliacao
                (id, criado_em, atualizado_em, avaliacao_id, tipo, valor, faixa_min, faixa_max)
            VALUES (:id, now(), now(), :aid, :tipo, :val, :fmin, :fmax)
        """), {
            "id": _novo_id(), "aid": avaliacao_id,
            "tipo": f"peso_{int(pt['idade_meses'])}m",
            "val": pt["peso_kg"], "fmin": pt["peso_min_kg"], "fmax": pt["peso_max_kg"],
        })


def processar_avaliacao(avaliacao_id: str) -> None:
    """Task RQ: executa pipeline e persiste resultado para a avaliacao dada."""
    engine = _db_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT parametros_entrada FROM avaliacao WHERE id = :id"),
            {"id": avaliacao_id},
        ).fetchone()
        if row is None:
            raise ValueError(f"avaliacao {avaliacao_id} nao encontrada")

        params = row[0]
        if isinstance(params, str):
            params = json.loads(params)

        kp_cm = {int(k): tuple(v) for k, v in params["kp_cm"].items()}
        try:
            resultado = montar_payload(
                avaliacao_id=avaliacao_id,
                kp_cm=kp_cm,
                sexo=params["sexo"],
                idade_meses=params["idade_meses"],
                largura_garupa_cm=params.get("largura_garupa_cm"),
                area_tronco_cm2=params.get("area_tronco_cm2"),
                largura_torax_cm=params.get("largura_torax_cm"),
            )
        except Exception as e:
            conn.execute(
                text(
                    "UPDATE avaliacao SET status = 'erro', observacoes = :obs,"
                    " atualizado_em = now() WHERE id = :id",
                ),
                {"obs": f"erro no pipeline: {e!s}", "id": avaliacao_id},
            )
            raise

        resultado_json = json.dumps(resultado)
        conn.execute(text("""
            UPDATE avaliacao
            SET resultado = :res::jsonb,
                versao_pipeline = :ver,
                status = 'concluida',
                atualizado_em = now()
            WHERE id = :id
        """), {"res": resultado_json, "ver": VERSAO_PIPELINE, "id": avaliacao_id})

        _salvar_estruturado(conn, avaliacao_id, resultado)
