"""Testes dos endpoints CRUD da Fase A + historico com GMD."""

from __future__ import annotations

import uuid
from datetime import date

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


def _criar_fazenda(client: TestClient, **extra) -> dict:
    payload = {"nome": "Fazenda Teste", "tipo": "fazenda", "bioma": "Pantanal", **extra}
    r = client.post("/fazendas", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _criar_animal(client: TestClient, fazenda_id: str, **extra) -> dict:
    payload = {
        "fazenda_id": fazenda_id,
        "sexo": "F",
        "nascimento": "2024-01-01",
        **extra,
    }
    r = client.post("/animais", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


# ------- Fazenda CRUD -------

def test_fazenda_crud_completo(client: TestClient) -> None:
    criada = _criar_fazenda(
        client,
        tipo="sitio",
        latitude="-19.123456",
        longitude="-57.654321",
        area_hectares="150.5",
        codigo_sisbov="BR076123",
    )
    assert criada["tipo"] == "sitio"
    fid = criada["id"]

    # list
    r = client.get("/fazendas")
    assert r.status_code == 200 and len(r.json()) == 1

    # get by id
    r = client.get(f"/fazendas/{fid}")
    assert r.status_code == 200 and r.json()["nome"] == "Fazenda Teste"

    # patch
    r = client.patch(f"/fazendas/{fid}", json={"bioma": "Cerrado", "tipo": "retiro"})
    assert r.status_code == 200
    assert r.json()["bioma"] == "Cerrado"
    assert r.json()["tipo"] == "retiro"

    # delete
    r = client.delete(f"/fazendas/{fid}")
    assert r.status_code == 204
    r = client.get(f"/fazendas/{fid}")
    assert r.status_code == 404


def test_fazenda_rejeita_latitude_invalida(client: TestClient) -> None:
    r = client.post("/fazendas", json={"nome": "x", "latitude": "95"})
    assert r.status_code == 422


# ------- Lote CRUD -------

def test_lote_crud_e_filtro_por_fazenda(client: TestClient) -> None:
    f = _criar_fazenda(client)
    r = client.post(
        "/lotes", json={"fazenda_id": f["id"], "nome": "L1", "categoria": "garrote"},
    )
    assert r.status_code == 201

    r = client.get(f"/lotes?fazenda_id={f['id']}")
    assert r.status_code == 200 and len(r.json()) == 1


# ------- Animal CRUD -------

def test_animal_crud(client: TestClient) -> None:
    f = _criar_fazenda(client)
    a = _criar_animal(
        client,
        f["id"],
        brinco="A001",
        rgn="RGN-123",
        ceip=True,
        data_entrada="2024-06-01",
    )
    assert a["brinco"] == "A001"
    assert a["ceip"] is True
    assert a["data_entrada"] == "2024-06-01"

    # patch
    r = client.patch(f"/animais/{a['id']}", json={"situacao": "vendido"})
    assert r.status_code == 200 and r.json()["situacao"] == "vendido"


def test_animal_lista_com_filtro_brinco(client: TestClient) -> None:
    f = _criar_fazenda(client)
    _criar_animal(client, f["id"], brinco="A001")
    _criar_animal(client, f["id"], brinco="A002")

    r = client.get("/animais?brinco=A002")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1 and body[0]["brinco"] == "A002"


# ------- Identificacao eletronica -------

def test_identificacao_eletronica_crud(client: TestClient) -> None:
    f = _criar_fazenda(client)
    a = _criar_animal(client, f["id"])

    payload = {
        "animal_id": a["id"],
        "eid": "076000012345678",  # ISO BR
        "vid": "A001",
        "modo": "FDX_B",
        "fabricante": "Allflex",
        "ativo_desde": "2024-06-01",
    }
    r = client.post("/identificacoes", json=payload)
    assert r.status_code == 201, r.text
    assert r.json()["eid"] == "076000012345678"

    r = client.get(f"/identificacoes?animal_id={a['id']}")
    assert r.status_code == 200 and len(r.json()) == 1


def test_identificacao_normaliza_eid_com_espacos(client: TestClient) -> None:
    f = _criar_fazenda(client)
    a = _criar_animal(client, f["id"])

    r = client.post(
        "/identificacoes",
        json={
            "animal_id": a["id"],
            "eid": "982 000012345678",
            "modo": "FDX_B",
            "ativo_desde": "2024-06-01",
        },
    )
    assert r.status_code == 201
    assert r.json()["eid"] == "982000012345678"


# ------- Dispositivo -------

def test_dispositivo_crud_balanca(client: TestClient) -> None:
    f = _criar_fazenda(client)
    r = client.post(
        "/dispositivos",
        json={
            "fazenda_id": f["id"],
            "tipo": "balanca",
            "modelo": "KM3-N",
            "fabricante": "Coimma",
            "numero_serie": "SN-12345",
            "config": {"porta_serial": "COM3", "baud": 9600},
        },
    )
    assert r.status_code == 201
    assert r.json()["config"]["baud"] == 9600


def test_dispositivo_filtro_por_tipo(client: TestClient) -> None:
    f = _criar_fazenda(client)
    client.post(
        "/dispositivos", json={"fazenda_id": f["id"], "tipo": "balanca", "modelo": "x"},
    )
    client.post(
        "/dispositivos",
        json={"fazenda_id": f["id"], "tipo": "gps_tracker", "modelo": "iBoi"},
    )
    r = client.get("/dispositivos?tipo=gps_tracker")
    assert r.status_code == 200
    assert len(r.json()) == 1 and r.json()[0]["tipo"] == "gps_tracker"


# ------- Pesagem + Historico/GMD -------

def test_pesagem_e_historico_calcula_gmd(client: TestClient) -> None:
    f = _criar_fazenda(client)
    a = _criar_animal(client, f["id"], nascimento="2024-01-01")

    # 3 pesagens espacadas: 100 kg (dia 0) -> 130 kg (+30d) -> 190 kg (+90d)
    for data_, peso in [
        ("2024-07-01", "100.00"),
        ("2024-07-31", "130.00"),
        ("2024-10-29", "190.00"),
    ]:
        r = client.post(
            "/pesagens",
            json={
                "animal_id": a["id"],
                "data": data_,
                "peso_kg": peso,
                "origem": "balanca",
            },
        )
        assert r.status_code == 201

    r = client.get(f"/animais/{a['id']}/historico")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["pesagens"]) == 3

    # Primeira pesagem sem GMD, segunda = 30/30=1.0, terceira = 60/90≈0.667
    assert body["pesagens"][0]["gmd_kg_dia"] is None
    assert body["pesagens"][1]["gmd_kg_dia"] == pytest.approx(1.0, abs=0.001)
    assert body["pesagens"][2]["gmd_kg_dia"] == pytest.approx(60 / 90, abs=0.001)

    # GMD total: (190 - 100) / 120 dias = 0.75 kg/dia
    assert body["gmd_total_kg_dia"] == pytest.approx(0.75, abs=0.001)
    assert float(body["peso_atual_kg"]) == pytest.approx(190.0)
    assert body["idade_dias"] is not None and body["idade_dias"] > 0


def test_historico_sem_pesagens(client: TestClient) -> None:
    f = _criar_fazenda(client)
    a = _criar_animal(client, f["id"])
    r = client.get(f"/animais/{a['id']}/historico")
    assert r.status_code == 200
    body = r.json()
    assert body["pesagens"] == []
    assert body["gmd_total_kg_dia"] is None
    assert body["peso_atual_kg"] is None


def test_historico_404_animal_nao_existe(client: TestClient) -> None:
    r = client.get(f"/animais/{uuid.uuid4()}/historico")
    assert r.status_code == 404


def test_pesagem_rejeita_peso_zero(client: TestClient) -> None:
    f = _criar_fazenda(client)
    a = _criar_animal(client, f["id"])
    r = client.post(
        "/pesagens",
        json={
            "animal_id": a["id"],
            "data": date.today().isoformat(),
            "peso_kg": "0",
            "origem": "balanca",
        },
    )
    assert r.status_code == 422
