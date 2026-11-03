"""Testes da Fase 3 — infraestrutura ML.

Cobre:
1. POST /modelos-versao → 201, campos corretos
2. GET /modelos-versao?nome=peso → lista
3. PATCH /modelos-versao/{id}/ativar → sets ativo=True
4. GET /avaliacoes/exportar-coco → estrutura COCO valida
5. GET /relatorio/acuracia → retorna dict com chave "metricas"
6. GET /relatorio/pesos → retorna dict com chave "n_pares"
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import get_db
from app.main import app
from app.models import Animal, Base, Fazenda
from app.models.enums import Sexo

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
def animal_e_fazenda(db_engine):
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    with SessionLocal() as s:
        fazenda = Fazenda(nome="Fazenda Teste Fase3", bioma="Cerrado")
        s.add(fazenda)
        s.flush()
        animal = Animal(fazenda_id=fazenda.id, sexo=Sexo.M, brinco="F3-001", rgn="RGN003")
        s.add(animal)
        s.commit()
        s.refresh(fazenda)
        s.refresh(animal)
        return fazenda, animal


def _kp_payload() -> list[dict]:
    pontos = {
        0: (10.0, 30.0), 1: (25.0, 25.0), 2: (55.0, 10.0), 3: (60.0, 20.0),
        4: (100.0, 25.0), 5: (120.0, 25.0), 6: (140.0, 25.0), 7: (180.0, 45.0),
        8: (190.0, 30.0), 9: (50.0, 40.0), 10: (80.0, 35.0), 11: (80.0, 95.0),
        12: (100.0, 85.0), 13: (90.0, 90.0), 14: (35.0, 80.0), 15: (30.0, 100.0),
        16: (165.0, 80.0), 17: (170.0, 100.0),
    }
    return [{"id": k, "x": x, "y": y} for k, (x, y) in pontos.items()]


def _avaliacao_base(animal_id: str) -> dict:
    return {
        "animal_id": animal_id,
        "data_hora": datetime.now(UTC).isoformat(),
        "sexo": "macho",
        "idade_meses": 24.0,
        "keypoints_cm": _kp_payload(),
        "px_por_cm": 5.0,
    }


# ---------------------------------------------------------------------------
# 1. POST /modelos-versao → 201
# ---------------------------------------------------------------------------


def test_criar_modelo_versao_retorna_201(client: TestClient) -> None:
    payload = {
        "nome": "peso",
        "versao": "0.1.0",
        "metricas": {"MAPE": 0.048, "MAE_kg": 18.2},
        "artefato_url": "s3://indexbeef/models/peso_v0.1.0.json",
        "ativo": False,
        "descricao": "Primeira versao LightGBM peso",
    }
    r = client.post("/modelos-versao", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["nome"] == "peso"
    assert body["versao"] == "0.1.0"
    assert body["ativo"] is False
    assert body["metricas"]["MAPE"] == pytest.approx(0.048)
    assert "id" in body
    assert "criado_em" in body


# ---------------------------------------------------------------------------
# 2. GET /modelos-versao?nome=peso → lista
# ---------------------------------------------------------------------------


def test_listar_modelos_versao_por_nome(client: TestClient) -> None:
    # Criar dois modelos com nomes diferentes
    client.post("/modelos-versao", json={"nome": "peso", "versao": "0.1.0"})
    client.post("/modelos-versao", json={"nome": "peso", "versao": "0.2.0"})
    client.post("/modelos-versao", json={"nome": "segmentacao", "versao": "0.1.0"})

    r = client.get("/modelos-versao?nome=peso")
    assert r.status_code == 200
    lista = r.json()
    assert len(lista) == 2
    assert all(m["nome"] == "peso" for m in lista)


def test_listar_modelos_versao_sem_filtro(client: TestClient) -> None:
    client.post("/modelos-versao", json={"nome": "keypoints_lateral", "versao": "0.1.0"})
    r = client.get("/modelos-versao")
    assert r.status_code == 200
    assert len(r.json()) >= 1


# ---------------------------------------------------------------------------
# 3. PATCH /modelos-versao/{id}/ativar
# ---------------------------------------------------------------------------


def test_ativar_modelo_versao(client: TestClient) -> None:
    r1 = client.post("/modelos-versao", json={"nome": "ecc", "versao": "0.1.0", "ativo": False})
    r2 = client.post("/modelos-versao", json={"nome": "ecc", "versao": "0.2.0", "ativo": False})
    id1 = r1.json()["id"]
    id2 = r2.json()["id"]

    # Ativar o segundo
    r = client.patch(f"/modelos-versao/{id2}/ativar")
    assert r.status_code == 200
    assert r.json()["ativo"] is True

    # O primeiro deve estar inativo
    r_get1 = client.get(f"/modelos-versao/{id1}")
    assert r_get1.json()["ativo"] is False

    # Agora ativar o primeiro — o segundo deve ficar inativo
    r = client.patch(f"/modelos-versao/{id1}/ativar")
    assert r.status_code == 200
    assert r.json()["ativo"] is True

    r_get2 = client.get(f"/modelos-versao/{id2}")
    assert r_get2.json()["ativo"] is False


def test_ativar_modelo_inexistente_retorna_404(client: TestClient) -> None:
    r = client.patch(f"/modelos-versao/{uuid.uuid4()}/ativar")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# 4. GET /avaliacoes/exportar-coco
# ---------------------------------------------------------------------------


def test_exportar_coco_estrutura_valida(
    client: TestClient, animal_e_fazenda: tuple,
) -> None:
    _, animal = animal_e_fazenda
    # Criar uma avaliacao com px_por_cm
    payload = _avaliacao_base(str(animal.id))
    r = client.post("/avaliacoes", json=payload)
    assert r.status_code == 201, r.text

    r_coco = client.get("/avaliacoes/exportar-coco")
    assert r_coco.status_code == 200
    body = r_coco.json()

    assert "images" in body
    assert "annotations" in body
    assert "categories" in body
    assert "info" in body

    # Verificar categoria
    assert len(body["categories"]) == 1
    cat = body["categories"][0]
    assert cat["name"] == "bovino_lateral"
    assert len(cat["keypoints"]) == 18

    # Deve ter pelo menos uma imagem e anotacao
    assert len(body["images"]) >= 1
    assert len(body["annotations"]) >= 1

    ann = body["annotations"][0]
    assert ann["category_id"] == 1
    assert ann["num_keypoints"] == 18
    assert len(ann["keypoints"]) == 18 * 3  # x,y,v para cada kp


def test_exportar_coco_filtro_fazenda(
    client: TestClient, animal_e_fazenda: tuple,
) -> None:
    fazenda, animal = animal_e_fazenda
    client.post("/avaliacoes", json=_avaliacao_base(str(animal.id)))

    # Filtrar pela fazenda correta
    r = client.get(f"/avaliacoes/exportar-coco?fazenda_id={fazenda.id}")
    assert r.status_code == 200
    body = r.json()
    assert len(body["images"]) >= 1

    # Filtrar por fazenda inexistente
    r2 = client.get(f"/avaliacoes/exportar-coco?fazenda_id={uuid.uuid4()}")
    assert r2.status_code == 200
    assert len(r2.json()["images"]) == 0


# ---------------------------------------------------------------------------
# 5. GET /relatorio/acuracia
# ---------------------------------------------------------------------------


def test_relatorio_acuracia_retorna_metricas(client: TestClient) -> None:
    r = client.get("/relatorio/acuracia")
    assert r.status_code == 200
    body = r.json()
    assert "metricas" in body
    assert "total_avaliacoes" in body
    assert "com_medidas_manuais" in body


def test_relatorio_acuracia_sem_dados(client: TestClient) -> None:
    r = client.get("/relatorio/acuracia")
    assert r.status_code == 200
    body = r.json()
    assert body["total_avaliacoes"] == 0
    assert body["com_medidas_manuais"] == 0
    # Metricas existem mas com n=0
    assert isinstance(body["metricas"], dict)


# ---------------------------------------------------------------------------
# 6. GET /relatorio/pesos
# ---------------------------------------------------------------------------


def test_relatorio_pesos_retorna_n_pares(client: TestClient) -> None:
    r = client.get("/relatorio/pesos")
    assert r.status_code == 200
    body = r.json()
    assert "n_pares" in body


def test_relatorio_pesos_sem_dados(client: TestClient) -> None:
    r = client.get("/relatorio/pesos")
    assert r.status_code == 200
    body = r.json()
    assert body["n_pares"] == 0
    assert body["mape_pct"] is None
