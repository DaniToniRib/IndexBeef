"""Testes dos modelos do IndexBeef (ver docs/06-modelo-de-dados.md)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Animal, Avaliacao, Captura, Fazenda, Lote, Pesagem
from app.models.enums import (
    CategoriaLote,
    OrigemPesagem,
    Sexo,
    SituacaoAnimal,
    StatusAvaliacao,
    TipoCaptura,
    Variedade,
    VistaCaptura,
)


def _seed_fazenda(db: Session) -> Fazenda:
    fazenda = Fazenda(nome="Fazenda Teste", municipio="Corumba", uf="MS", bioma="Pantanal")
    db.add(fazenda)
    db.flush()
    return fazenda


def test_fazenda_cria_e_tem_timestamps(db: Session) -> None:
    f = _seed_fazenda(db)
    db.commit()
    db.refresh(f)
    assert isinstance(f.id, uuid.UUID)
    assert f.criado_em is not None
    assert f.atualizado_em is not None
    assert f.sincronizado_em is None


def test_lote_pertence_a_fazenda(db: Session) -> None:
    fazenda = _seed_fazenda(db)
    lote = Lote(fazenda_id=fazenda.id, nome="Lote 01", categoria=CategoriaLote.garrote)
    db.add(lote)
    db.commit()
    db.refresh(fazenda)
    assert lote.fazenda_id == fazenda.id
    assert len(fazenda.lotes) == 1
    assert fazenda.lotes[0].categoria == CategoriaLote.garrote


def test_animal_com_pai_e_mae(db: Session) -> None:
    fazenda = _seed_fazenda(db)
    pai = Animal(fazenda_id=fazenda.id, sexo=Sexo.M, raca="Nelore", variedade=Variedade.padrao)
    mae = Animal(fazenda_id=fazenda.id, sexo=Sexo.F, raca="Nelore")
    db.add_all([pai, mae])
    db.flush()

    bezerro = Animal(
        fazenda_id=fazenda.id,
        sexo=Sexo.M,
        brinco="A001",
        rgn="RGN-123",
        ceip=True,
        nascimento=date(2025, 7, 1),
        pai_id=pai.id,
        mae_id=mae.id,
    )
    db.add(bezerro)
    db.commit()
    db.refresh(bezerro)

    assert bezerro.pai is not None and bezerro.pai.id == pai.id
    assert bezerro.mae is not None and bezerro.mae.id == mae.id
    assert bezerro.situacao == SituacaoAnimal.ativo
    assert bezerro.raca == "Nelore"


def test_pesagem_balanca(db: Session) -> None:
    fazenda = _seed_fazenda(db)
    animal = Animal(fazenda_id=fazenda.id, sexo=Sexo.F)
    db.add(animal)
    db.flush()

    pesagem = Pesagem(
        animal_id=animal.id,
        data=date(2026, 10, 15),
        peso_kg=Decimal("412.50"),
        origem=OrigemPesagem.balanca,
    )
    db.add(pesagem)
    db.commit()
    db.refresh(animal)
    assert len(animal.pesagens) == 1
    assert animal.pesagens[0].peso_kg == Decimal("412.50")
    assert animal.pesagens[0].origem == OrigemPesagem.balanca


def test_avaliacao_com_capturas(db: Session) -> None:
    fazenda = _seed_fazenda(db)
    animal = Animal(fazenda_id=fazenda.id, sexo=Sexo.M)
    db.add(animal)
    db.flush()

    av = Avaliacao(
        animal_id=animal.id,
        data_hora=datetime(2026, 10, 20, 9, 30, tzinfo=timezone.utc),
        versao_pipeline="0.1.0",
    )
    db.add(av)
    db.flush()

    db.add_all(
        [
            Captura(
                avaliacao_id=av.id,
                tipo=TipoCaptura.video,
                vista=VistaCaptura.lateral,
                arquivo_url="s3://indexbeef/av1/lat.mp4",
                px_por_cm=Decimal("4.1200"),
                erro_calibracao_px=Decimal("0.8000"),
            ),
            Captura(
                avaliacao_id=av.id,
                tipo=TipoCaptura.foto,
                vista=VistaCaptura.traseira,
                arquivo_url="s3://indexbeef/av1/tras.jpg",
            ),
        ],
    )
    db.commit()
    db.refresh(av)

    assert av.status == StatusAvaliacao.capturada
    assert len(av.capturas) == 2
    vistas = {c.vista for c in av.capturas}
    assert vistas == {VistaCaptura.lateral, VistaCaptura.traseira}


def test_cascade_delete_fazenda_remove_lotes_e_animais(db: Session) -> None:
    fazenda = _seed_fazenda(db)
    lote = Lote(fazenda_id=fazenda.id, nome="L1", categoria=CategoriaLote.matriz)
    db.add(lote)
    db.flush()
    animal = Animal(fazenda_id=fazenda.id, lote_id=lote.id, sexo=Sexo.F)
    db.add(animal)
    db.commit()

    db.delete(fazenda)
    db.commit()

    assert db.scalar(select(Fazenda).where(Fazenda.id == fazenda.id)) is None
    assert db.scalar(select(Lote).where(Lote.id == lote.id)) is None
    assert db.scalar(select(Animal).where(Animal.id == animal.id)) is None


def test_pesagem_vinculada_a_avaliacao_estimada(db: Session) -> None:
    fazenda = _seed_fazenda(db)
    animal = Animal(fazenda_id=fazenda.id, sexo=Sexo.M)
    db.add(animal)
    db.flush()

    av = Avaliacao(animal_id=animal.id, data_hora=datetime.now(timezone.utc))
    db.add(av)
    db.flush()

    pes = Pesagem(
        animal_id=animal.id,
        data=date(2026, 10, 20),
        peso_kg=Decimal("380.00"),
        origem=OrigemPesagem.estimado,
        avaliacao_id=av.id,
    )
    db.add(pes)
    db.commit()
    db.refresh(av)
    assert len(av.pesagens) == 1
    assert av.pesagens[0].avaliacao_id == av.id


@pytest.mark.parametrize("enum_cls", [CategoriaLote, Sexo, StatusAvaliacao, TipoCaptura])
def test_enums_tem_valores_do_docs06(enum_cls: type) -> None:
    assert len(list(enum_cls)) >= 2
