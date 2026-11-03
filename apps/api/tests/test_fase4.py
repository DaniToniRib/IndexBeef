"""Testes da Fase 4 — indices de aptidao, GMD, projecao de peso e matrizes prenhes.

Cobre:
1.  calcular_frame_score: macho jovem
2.  calcular_frame_score: femea adulta
3.  calcular_frame_score: idade < 1 mes -> None
4.  calcular_frame_score: clamp em 9.0
5.  sugerir_epmuras: medidas completas retorna dict com chaves EPMURAS
6.  sugerir_epmuras: R/A/S sempre None
7.  calcular_gmd: lista de 2 pesagens
8.  calcular_gmd: lista de 1 pesagem -> None
9.  calcular_projecao_brody: retorna lista com tamanho correto
10. calcular_projecao_brody: sem projecoes no passado
11. POST /indices/avaliacoes/{id}/calcular -> 201, body com indices
12. POST /indices/avaliacoes/{id}/calcular: avaliacao inexistente -> 404
13. GET /lotes/{lote_id}/ranking?indice=garrote: retorna lista ordenada
14. GET /lotes/{lote_id}/matrizes-prenhes: retorna prenhe mas nao sem diagnostico
15. GET /animais/{id}/gmd: sem pesagens retorna null
16. GET /animais/{id}/projecao-peso: retorna projecoes com 3 pontos
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import get_db
from app.main import app
from app.models import Animal, Base, Fazenda
from app.models.avaliacao import Avaliacao
from app.models.caixa_virtual_avaliacao import CaixaVirtualAvaliacao
from app.models.enums import (
    CategoriaLote,
    OrigemPesagem,
    Sexo,
    StatusAvaliacao,
    TipoEventoReprodutivo,
)
from app.models.escore_avaliacao import EscoreAvaliacao
from app.models.evento_reprodutivo import EventoReprodutivo
from app.models.lote import Lote
from app.models.medida_avaliacao import MedidaAvaliacao
from app.models.pesagem import Pesagem
from app.services.indices_service import (
    _cfg,
    calcular_frame_score,
    calcular_gmd,
    calcular_projecao_brody,
    sugerir_epmuras,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def client(db_engine):
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        s = SessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    with SessionLocal() as s:
        yield s


@pytest.fixture
def setup_lote_animal(db_engine):
    """Cria fazenda, lote, animal macho e avaliacao com dados basicos."""
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    with SessionLocal() as s:
        fazenda = Fazenda(nome="Fazenda Fase4", bioma="Pantanal")
        s.add(fazenda)
        s.flush()

        lote = Lote(fazenda_id=fazenda.id, nome="Lote A", categoria=CategoriaLote.garrote)
        s.add(lote)
        s.flush()

        nascimento = date(2025, 1, 1)
        animal = Animal(
            fazenda_id=fazenda.id,
            lote_id=lote.id,
            sexo=Sexo.M,
            brinco="F4-001",
            nascimento=nascimento,
        )
        s.add(animal)
        s.flush()

        avaliacao = Avaliacao(
            animal_id=animal.id,
            data_hora=datetime(2026, 11, 3, 10, 0, tzinfo=UTC),
            status=StatusAvaliacao.concluida,
        )
        s.add(avaliacao)
        s.flush()

        medida = MedidaAvaliacao(
            avaliacao_id=avaliacao.id,
            altura_cernelha_cm=130,
            altura_garupa_cm=132,
            comprimento_corporal_cm=155,
            largura_garupa_cm=42,
            umbigo_chao_cm=48,
        )
        s.add(medida)

        caixa = CaixaVirtualAvaliacao(
            avaliacao_id=avaliacao.id,
            volume_l=220,
            ipl=1.8,
            compacidade=1.05,
        )
        s.add(caixa)

        s.commit()
        s.refresh(fazenda)
        s.refresh(lote)
        s.refresh(animal)
        s.refresh(avaliacao)
        return fazenda, lote, animal, avaliacao


# ---------------------------------------------------------------------------
# 1. calcular_frame_score: macho jovem
# ---------------------------------------------------------------------------


def test_frame_score_macho_jovem() -> None:
    nascimento = date(2025, 5, 1)
    data = date(2026, 11, 1)
    fs = calcular_frame_score(130.0, "M", nascimento, data)
    assert fs is not None
    assert 1.0 <= fs <= 9.0


# ---------------------------------------------------------------------------
# 2. calcular_frame_score: femea adulta
# ---------------------------------------------------------------------------


def test_frame_score_femea_adulta() -> None:
    nascimento = date(2022, 1, 1)
    data = date(2026, 11, 3)
    fs = calcular_frame_score(140.0, "F", nascimento, data)
    assert fs is not None
    assert 1.0 <= fs <= 9.0


# ---------------------------------------------------------------------------
# 3. calcular_frame_score: idade < 1 mes -> None
# ---------------------------------------------------------------------------


def test_frame_score_muito_novo_retorna_none() -> None:
    nascimento = date(2026, 11, 2)
    data = date(2026, 11, 3)
    fs = calcular_frame_score(80.0, "M", nascimento, data)
    assert fs is None


# ---------------------------------------------------------------------------
# 4. calcular_frame_score: clamp em 9.0
# ---------------------------------------------------------------------------


def test_frame_score_clamp_maximo() -> None:
    nascimento = date(2024, 1, 1)
    data = date(2026, 11, 3)
    fs = calcular_frame_score(200.0, "M", nascimento, data)
    assert fs == 9.0


# ---------------------------------------------------------------------------
# 5. sugerir_epmuras: medidas completas retorna dict com chaves EPMURAS
# ---------------------------------------------------------------------------


def test_sugerir_epmuras_medidas_completas() -> None:
    medidas = {
        "largura_garupa_cm": 42.0,
        "comprimento_corporal_cm": 155.0,
        "umbigo_chao_cm": 50.0,
        "altura_cernelha_cm": 130.0,
    }
    caixa = {"volume_l": 220.0, "compacidade": 1.05}
    resultado = sugerir_epmuras(medidas, caixa)
    assert set(resultado.keys()) == {"E", "P", "M", "U", "R", "A", "S"}
    assert resultado["E"] is not None
    assert resultado["P"] is not None
    assert resultado["M"] is not None
    assert resultado["U"] is not None


# ---------------------------------------------------------------------------
# 6. sugerir_epmuras: R/A/S sempre None
# ---------------------------------------------------------------------------


def test_sugerir_epmuras_ras_none() -> None:
    resultado = sugerir_epmuras({}, {})
    assert resultado["R"] is None
    assert resultado["A"] is None
    assert resultado["S"] is None


# ---------------------------------------------------------------------------
# 7. calcular_gmd: lista de 2 pesagens
# ---------------------------------------------------------------------------


def test_calcular_gmd_duas_pesagens() -> None:
    pesagens = [
        {"data": date(2026, 1, 1), "peso_kg": 200.0},
        {"data": date(2026, 7, 1), "peso_kg": 320.0},
    ]
    gmd = calcular_gmd(pesagens)
    assert gmd is not None
    assert gmd == pytest.approx(120.0 / 181, rel=1e-3)


# ---------------------------------------------------------------------------
# 8. calcular_gmd: lista de 1 pesagem -> None
# ---------------------------------------------------------------------------


def test_calcular_gmd_uma_pesagem_retorna_none() -> None:
    pesagens = [{"data": date(2026, 1, 1), "peso_kg": 200.0}]
    assert calcular_gmd(pesagens) is None


# ---------------------------------------------------------------------------
# 9. calcular_projecao_brody: retorna lista com tamanho correto
# ---------------------------------------------------------------------------


def test_projecao_brody_tamanho_correto() -> None:
    cfg = _cfg()
    projecoes = calcular_projecao_brody(250.0, "M", 18.0, 5.0, cfg)
    idades_alvo = cfg["projecao"]["idades_alvo_meses"]
    esperadas = [i for i in idades_alvo if i > 18]
    assert len(projecoes) == len(esperadas)
    for p in projecoes:
        assert "idade_meses" in p
        assert "peso_kg" in p
        assert "peso_min_kg" in p
        assert "peso_max_kg" in p


# ---------------------------------------------------------------------------
# 10. calcular_projecao_brody: sem projecoes no passado
# ---------------------------------------------------------------------------


def test_projecao_brody_sem_passado() -> None:
    cfg = _cfg()
    projecoes = calcular_projecao_brody(450.0, "M", 30.0, 5.0, cfg)
    for p in projecoes:
        assert p["idade_meses"] > 30


# ---------------------------------------------------------------------------
# 11. POST /indices/avaliacoes/{id}/calcular -> 201, body com indices
# ---------------------------------------------------------------------------


def test_calcular_indices_retorna_201(
    client: TestClient, setup_lote_animal: tuple,
) -> None:
    _, _, _, avaliacao = setup_lote_animal
    r = client.post(f"/indices/avaliacoes/{avaliacao.id}/calcular")
    assert r.status_code == 201, r.text
    body = r.json()
    assert "avaliacao_id" in body
    assert "frame_score" in body
    assert "epmuras_sugerido" in body
    assert "gmd_kg_dia" in body
    assert "indices" in body
    assert len(body["indices"]) >= 1
    for idx in body["indices"]:
        assert "tipo" in idx
        assert "valor" in idx
        assert "explicacao" in idx


# ---------------------------------------------------------------------------
# 12. POST /indices/avaliacoes/{id}/calcular: avaliacao inexistente -> 404
# ---------------------------------------------------------------------------


def test_calcular_indices_avaliacao_inexistente_retorna_404(client: TestClient) -> None:
    r = client.post(f"/indices/avaliacoes/{uuid.uuid4()}/calcular")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# 13. GET /lotes/{lote_id}/ranking?indice=garrote: retorna lista ordenada
# ---------------------------------------------------------------------------


def test_ranking_lote_garrote(
    client: TestClient, setup_lote_animal: tuple,
) -> None:
    _, lote, _, avaliacao = setup_lote_animal
    client.post(f"/indices/avaliacoes/{avaliacao.id}/calcular")

    r = client.get(f"/lotes/{lote.id}/ranking?indice=garrote")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "total" in body
    assert "itens" in body
    assert body["total"] >= 1
    if body["total"] > 1:
        valores = [item["valor"] for item in body["itens"]]
        assert valores == sorted(valores, reverse=True)


# ---------------------------------------------------------------------------
# 14. GET /lotes/{lote_id}/matrizes-prenhes
# ---------------------------------------------------------------------------


def test_matrizes_prenhes(
    client: TestClient, db_engine, setup_lote_animal: tuple,
) -> None:
    _, lote, _, _ = setup_lote_animal

    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    with SessionLocal() as s:
        fazenda_id = lote.fazenda_id
        animal_prenhe = Animal(
            fazenda_id=fazenda_id,
            lote_id=lote.id,
            sexo=Sexo.F,
            brinco="PRENHE-001",
            nascimento=date(2022, 6, 1),
        )
        s.add(animal_prenhe)
        s.flush()

        evento = EventoReprodutivo(
            animal_id=animal_prenhe.id,
            tipo=TipoEventoReprodutivo.diagnostico_gestacao,
            data=date(2026, 10, 1),
            resultado="positivo",
        )
        s.add(evento)

        animal_sem_diag = Animal(
            fazenda_id=fazenda_id,
            lote_id=lote.id,
            sexo=Sexo.F,
            brinco="SEM-DIAG-001",
            nascimento=date(2022, 6, 1),
        )
        s.add(animal_sem_diag)
        s.commit()

    r = client.get(f"/lotes/{lote.id}/matrizes-prenhes")
    assert r.status_code == 200, r.text
    body = r.json()
    brincos = [m["brinco"] for m in body]
    assert "PRENHE-001" in brincos
    assert "SEM-DIAG-001" not in brincos


# ---------------------------------------------------------------------------
# 15. GET /animais/{id}/gmd: sem pesagens retorna null
# ---------------------------------------------------------------------------


def test_gmd_sem_pesagens(
    client: TestClient, setup_lote_animal: tuple,
) -> None:
    _, _, animal, _ = setup_lote_animal
    r = client.get(f"/animais/{animal.id}/gmd")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["gmd_kg_dia"] is None
    assert body["pesagens"] == []


# ---------------------------------------------------------------------------
# 16. GET /animais/{id}/projecao-peso: retorna projecoes com 3 pontos
# ---------------------------------------------------------------------------


def test_projecao_peso_retorna_projecoes(
    client: TestClient, db_engine, setup_lote_animal: tuple,
) -> None:
    _, lote, _, _ = setup_lote_animal

    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    with SessionLocal() as s:
        fazenda_id = lote.fazenda_id
        animal_jovem = Animal(
            fazenda_id=fazenda_id,
            lote_id=lote.id,
            sexo=Sexo.M,
            brinco="JOVEM-001",
            nascimento=date(2026, 6, 1),
        )
        s.add(animal_jovem)
        s.flush()
        pesagem = Pesagem(
            animal_id=animal_jovem.id,
            data=date(2026, 11, 1),
            peso_kg=120.0,
            origem=OrigemPesagem.balanca,
        )
        s.add(pesagem)
        s.commit()
        s.refresh(animal_jovem)
        animal_id = animal_jovem.id

    r = client.get(f"/animais/{animal_id}/projecao-peso")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "peso_atual_kg" in body
    assert "projecoes" in body
    assert len(body["projecoes"]) == 3
    for p in body["projecoes"]:
        assert "idade_meses" in p
        assert "peso_kg" in p
        assert "peso_min_kg" in p
        assert "peso_max_kg" in p
