"""Testes GPS/geofence/eventos (Fase D)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import get_db
from app.main import app
from app.models import Base


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
def fazenda_animal(client: TestClient) -> tuple[str, str]:
    f = client.post("/fazendas", json={"nome": "F1", "tipo": "fazenda"}).json()
    a = client.post("/animais", json={"fazenda_id": f["id"], "sexo": "F"}).json()
    return f["id"], a["id"]


# Poligono quadrado em volta de (-19.0, -57.0) com 0.01° de lado
# (approx 1 km x 1 km no Pantanal). WKT em ordem (lon, lat).
_WKT_QUADRADO = (
    "POLYGON((-57.01 -19.01, -56.99 -19.01, -56.99 -18.99, -57.01 -18.99, "
    "-57.01 -19.01))"
)


# ------- Geofence CRUD + validacao WKT -------

def test_geofence_crud(client: TestClient, fazenda_animal) -> None:
    fid, _ = fazenda_animal
    r = client.post(
        "/geofences",
        json={
            "fazenda_id": fid,
            "nome": "Pasto 01",
            "tipo": "pasto",
            "poligono_wkt": _WKT_QUADRADO,
        },
    )
    assert r.status_code == 201, r.text
    gid = r.json()["id"]

    r = client.patch(f"/geofences/{gid}", json={"ativa": False})
    assert r.status_code == 200 and r.json()["ativa"] is False

    r = client.get(f"/geofences?fazenda_id={fid}")
    assert r.status_code == 200 and len(r.json()) == 1


def test_geofence_rejeita_wkt_invalido(client: TestClient, fazenda_animal) -> None:
    fid, _ = fazenda_animal
    r = client.post(
        "/geofences",
        json={
            "fazenda_id": fid,
            "nome": "x",
            "poligono_wkt": "banana",
        },
    )
    assert r.status_code == 422


def test_geofence_rejeita_geometria_nao_poligonal(client: TestClient, fazenda_animal) -> None:
    fid, _ = fazenda_animal
    r = client.post(
        "/geofences",
        json={
            "fazenda_id": fid,
            "nome": "x",
            "poligono_wkt": "POINT(-57 -19)",
        },
    )
    assert r.status_code == 422
    assert "POLYGON" in r.text


# ------- Ingestao GPS + evento geofence -------

def _ponto(animal_id: str, dias_atras: float, lat: str, lon: str, bateria: int = 80) -> dict:
    ts = (datetime.now(UTC) - timedelta(days=dias_atras)).isoformat()
    return {
        "animal_id": animal_id,
        "timestamp": ts,
        "latitude": lat,
        "longitude": lon,
        "bateria_pct": bateria,
    }


def test_ingestao_gera_entrada_no_pasto(client: TestClient, fazenda_animal) -> None:
    fid, aid = fazenda_animal
    client.post(
        "/geofences",
        json={
            "fazenda_id": fid,
            "nome": "Pasto",
            "tipo": "pasto",
            "poligono_wkt": _WKT_QUADRADO,
        },
    )

    # Ponto 1 fora, ponto 2 dentro -> evento de entrada
    r = client.post(
        "/gps/pontos",
        json={
            "pontos": [
                _ponto(aid, 2, "-18.50", "-56.50"),  # fora (lat>-18.99)
                _ponto(aid, 1, "-19.00", "-57.00"),  # dentro
            ],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["importados"] == 2
    assert body["eventos_geofence_gerados"] == 1

    r = client.get(f"/animais/{aid}/eventos-geofence")
    body = r.json()
    assert len(body) == 1
    assert body[0]["tipo"] == "entrada"


def test_entrada_e_depois_saida(client: TestClient, fazenda_animal) -> None:
    fid, aid = fazenda_animal
    client.post(
        "/geofences",
        json={
            "fazenda_id": fid,
            "nome": "Pasto",
            "poligono_wkt": _WKT_QUADRADO,
        },
    )

    # (1) fora, (2) dentro -> entrada; (3) fora -> saida
    r = client.post(
        "/gps/pontos",
        json={
            "pontos": [
                _ponto(aid, 3, "-18.50", "-56.50"),
                _ponto(aid, 2, "-19.00", "-57.00"),
                _ponto(aid, 1, "-18.50", "-56.50"),
            ],
        },
    )
    assert r.json()["eventos_geofence_gerados"] == 2
    eventos = client.get(f"/animais/{aid}/eventos-geofence").json()
    tipos = [e["tipo"] for e in eventos]
    assert sorted(tipos) == ["entrada", "saida"]


def test_sem_geofence_nao_gera_evento(client: TestClient, fazenda_animal) -> None:
    _, aid = fazenda_animal
    r = client.post(
        "/gps/pontos",
        json={"pontos": [_ponto(aid, 1, "-19.00", "-57.00")]},
    )
    assert r.status_code == 201
    assert r.json()["eventos_geofence_gerados"] == 0


def test_geofence_inativa_nao_gera_evento(client: TestClient, fazenda_animal) -> None:
    fid, aid = fazenda_animal
    gf = client.post(
        "/geofences",
        json={
            "fazenda_id": fid,
            "nome": "x",
            "poligono_wkt": _WKT_QUADRADO,
            "ativa": False,
        },
    ).json()
    assert gf["ativa"] is False

    r = client.post(
        "/gps/pontos",
        json={"pontos": [_ponto(aid, 1, "-19.00", "-57.00")]},
    )
    assert r.json()["eventos_geofence_gerados"] == 0


def test_alerta_bateria_baixa(client: TestClient, fazenda_animal) -> None:
    _, aid = fazenda_animal
    r = client.post(
        "/gps/pontos",
        json={"pontos": [_ponto(aid, 1, "-19.00", "-57.00", bateria=10)]},
    )
    body = r.json()
    assert len(body["alertas"]) == 1
    assert body["alertas"][0]["tipo"] == "bateria_baixa"


def test_listar_pontos_filtro_por_animal(client: TestClient, fazenda_animal) -> None:
    _, aid = fazenda_animal
    client.post(
        "/gps/pontos",
        json={
            "pontos": [
                _ponto(aid, 2, "-19.00", "-57.00"),
                _ponto(aid, 1, "-19.00", "-57.01"),
            ],
        },
    )
    r = client.get(f"/gps/pontos?animal_id={aid}")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_rejeita_latitude_invalida(client: TestClient, fazenda_animal) -> None:
    _, aid = fazenda_animal
    r = client.post(
        "/gps/pontos",
        json={"pontos": [_ponto(aid, 1, "95", "-57.00")]},  # lat > 90
    )
    assert r.status_code == 422
