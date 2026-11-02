"""Testes dos endpoints POST /avaliacoes e GET /avaliacoes/{id}."""

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


@pytest.fixture
def db_engine():
    # StaticPool + check_same_thread=False -> funciona com TestClient em
    # outra thread e mantem o banco in-memory compartilhado nos requests.
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
def animal_persistido(db_engine) -> Animal:
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    with SessionLocal() as s:
        fazenda = Fazenda(nome="Fazenda Teste", bioma="Pantanal")
        s.add(fazenda)
        s.flush()
        animal = Animal(fazenda_id=fazenda.id, sexo=Sexo.F)
        s.add(animal)
        s.commit()
        s.refresh(animal)
        return animal


def _kp_payload() -> list[dict]:
    # Mesmo animal sintetico das Fase 0 (coordenadas em cm no plano da placa).
    pontos = {
        0: (10.0, 30.0),
        1: (25.0, 25.0),
        2: (55.0, 10.0),
        3: (60.0, 20.0),
        4: (100.0, 25.0),
        5: (120.0, 25.0),
        6: (140.0, 25.0),
        7: (180.0, 45.0),
        8: (190.0, 30.0),
        9: (50.0, 40.0),
        10: (80.0, 35.0),
        11: (80.0, 95.0),
        12: (100.0, 85.0),
        13: (90.0, 90.0),
        14: (35.0, 80.0),
        15: (30.0, 100.0),
        16: (165.0, 80.0),
        17: (170.0, 100.0),
    }
    return [{"id": kid, "x": x, "y": y} for kid, (x, y) in pontos.items()]


def test_post_cria_avaliacao_e_retorna_resultado(client: TestClient, animal_persistido) -> None:
    payload = {
        "animal_id": str(animal_persistido.id),
        "data_hora": datetime.now(UTC).isoformat(),
        "sexo": "femea",
        "idade_meses": 18.0,
        "keypoints_cm": _kp_payload(),
    }
    r = client.post("/avaliacoes", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "concluida"
    assert body["versao_pipeline"] == "0.1.0"
    assert body["resultado"] is not None
    assert body["resultado"]["medidas_cm"]["altura_cernelha"]["valor"] == pytest.approx(80.0)
    assert body["resultado"]["peso"]["peso_kg"] > 0
    assert len(body["resultado"]["projecao_peso"]["pontos"]) == 3


def test_get_retorna_avaliacao_persistida(client: TestClient, animal_persistido) -> None:
    payload = {
        "animal_id": str(animal_persistido.id),
        "data_hora": datetime.now(UTC).isoformat(),
        "sexo": "femea",
        "idade_meses": 18.0,
        "keypoints_cm": _kp_payload(),
    }
    r1 = client.post("/avaliacoes", json=payload)
    assert r1.status_code == 201
    aid = r1.json()["id"]

    r2 = client.get(f"/avaliacoes/{aid}")
    assert r2.status_code == 200
    body = r2.json()
    assert body["id"] == aid
    assert body["status"] == "concluida"
    assert body["resultado"]["peso"]["peso_kg"] == pytest.approx(
        r1.json()["resultado"]["peso"]["peso_kg"],
    )


def test_get_404_quando_nao_existe(client: TestClient) -> None:
    r = client.get(f"/avaliacoes/{uuid.uuid4()}")
    assert r.status_code == 404


def test_post_422_quando_falta_keypoint(client: TestClient, animal_persistido) -> None:
    # Remove um keypoint -> Pydantic rejeita (min_length=18)
    kp = _kp_payload()[:17]
    payload = {
        "animal_id": str(animal_persistido.id),
        "data_hora": datetime.now(UTC).isoformat(),
        "sexo": "femea",
        "idade_meses": 18.0,
        "keypoints_cm": kp,
    }
    r = client.post("/avaliacoes", json=payload)
    assert r.status_code == 422


def test_post_400_quando_ids_de_keypoints_duplicados(
    client: TestClient, animal_persistido,
) -> None:
    # 18 pontos mas com um ID duplicado (0) e sem o 17.
    kp = _kp_payload()
    kp[-1] = {"id": 0, "x": 10.0, "y": 30.0}
    payload = {
        "animal_id": str(animal_persistido.id),
        "data_hora": datetime.now(UTC).isoformat(),
        "sexo": "femea",
        "idade_meses": 18.0,
        "keypoints_cm": kp,
    }
    r = client.post("/avaliacoes", json=payload)
    assert r.status_code == 400
    assert "0..17" in r.json()["detail"]


def test_post_rejeita_idade_negativa(client: TestClient, animal_persistido) -> None:
    payload = {
        "animal_id": str(animal_persistido.id),
        "data_hora": datetime.now(UTC).isoformat(),
        "sexo": "femea",
        "idade_meses": -1.0,
        "keypoints_cm": _kp_payload(),
    }
    r = client.post("/avaliacoes", json=payload)
    assert r.status_code == 422  # Pydantic (gt=0)
