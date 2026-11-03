"""Testes dos endpoints de ingestao RFID + CSV de balanca (Fase B)."""

from __future__ import annotations

import io
from datetime import UTC, datetime

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
def animal_com_eid(client: TestClient) -> dict:
    """Cria fazenda + animal + identificacao eletronica ativa com EID 076..."""
    f = client.post("/fazendas", json={"nome": "F1", "tipo": "fazenda"}).json()
    a = client.post(
        "/animais",
        json={"fazenda_id": f["id"], "sexo": "F", "brinco": "A001"},
    ).json()
    client.post(
        "/identificacoes",
        json={
            "animal_id": a["id"],
            "eid": "076000012345678",
            "vid": "A001",
            "modo": "FDX_B",
            "ativo_desde": "2024-01-01",
        },
    )
    return a


# ------- POST /leituras/rfid (lote JSON) -------

def test_leitura_rfid_lote_pareia(client: TestClient, animal_com_eid) -> None:
    r = client.post(
        "/leituras/rfid",
        json={
            "leituras": [
                {
                    "eid": "076000012345678",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                {
                    "eid": "076999999999999",  # nao cadastrado
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            ],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert len(body) == 2
    assert body[0]["animal_id"] == animal_com_eid["id"]
    assert body[0]["pareado_em"] is not None
    assert body[1]["animal_id"] is None


def test_leitura_rfid_lote_normaliza_eid(client: TestClient, animal_com_eid) -> None:
    r = client.post(
        "/leituras/rfid",
        json={
            "leituras": [
                {
                    "eid": "076 00001-2345678",  # com espaço e hifen
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            ],
        },
    )
    assert r.status_code == 201
    assert r.json()[0]["eid"] == "076000012345678"
    assert r.json()[0]["animal_id"] == animal_com_eid["id"]


# ------- POST /leituras/rfid/importar-csv -------

def _csv_bastao_allflex(linhas: list[dict]) -> bytes:
    buf = io.StringIO()
    buf.write("EID,VID,Date,Time,Session\n")
    for lin in linhas:
        buf.write(
            f"{lin['eid']},{lin.get('vid','')},{lin['date']},"
            f"{lin['time']},{lin.get('session','')}\n",
        )
    return buf.getvalue().encode("utf-8")


def test_importar_csv_bastao(client: TestClient, animal_com_eid) -> None:
    csv_bytes = _csv_bastao_allflex(
        [
            {
                "eid": "076000012345678",
                "vid": "A001",
                "date": "2026-04-15",
                "time": "09:30:00",
                "session": "manejo-01",
            },
            {
                "eid": "076999999999999",
                "date": "2026-04-15",
                "time": "09:31:00",
                "session": "manejo-01",
            },
        ],
    )
    r = client.post(
        "/leituras/rfid/importar-csv",
        files={"arquivo": ("bastao.csv", csv_bytes, "text/csv")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["importadas"] == 2
    assert body["pareadas"] == 1
    assert body["erros"] == []

    # Confere persistencia + match
    r = client.get("/leituras/rfid?pareado=true")
    assert r.status_code == 200 and len(r.json()) == 1
    r = client.get("/leituras/rfid?pareado=false")
    assert r.status_code == 200 and len(r.json()) == 1


def test_csv_bastao_rejeita_sem_cabecalho_eid(client: TestClient) -> None:
    csv_bytes = b"foo,bar\n1,2\n"
    r = client.post(
        "/leituras/rfid/importar-csv",
        files={"arquivo": ("bad.csv", csv_bytes, "text/csv")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["importadas"] == 0
    assert any("EID" in e["motivo"] for e in body["erros"])


def test_csv_bastao_erros_por_linha(client: TestClient) -> None:
    csv_bytes = b"EID,Date,Time\n076000012345678,,09:30:00\n"
    r = client.post(
        "/leituras/rfid/importar-csv",
        files={"arquivo": ("x.csv", csv_bytes, "text/csv")},
    )
    body = r.json()
    assert body["importadas"] == 0
    assert len(body["erros"]) == 1


def test_csv_bastao_formato_br_data(client: TestClient, animal_com_eid) -> None:
    csv_bytes = b"EID,Date,Time\n076000012345678,15/04/2026,09:30:00\n"
    r = client.post(
        "/leituras/rfid/importar-csv",
        files={"arquivo": ("x.csv", csv_bytes, "text/csv")},
    )
    assert r.status_code == 200
    assert r.json()["importadas"] == 1
    assert r.json()["pareadas"] == 1


# ------- POST /pesagens/importar-csv (Tru-Test/Coimma) -------

def _csv_balanca_trutest(linhas: list[dict]) -> bytes:
    buf = io.StringIO()
    buf.write("VID,EID,Weight,Date,Time,Session\n")
    for lin in linhas:
        buf.write(
            f"{lin.get('vid','')},{lin.get('eid','')},{lin['weight']},"
            f"{lin['date']},{lin.get('time','')},{lin.get('session','')}\n",
        )
    return buf.getvalue().encode("utf-8")


def test_importar_csv_balanca_match_via_eid(client: TestClient, animal_com_eid) -> None:
    csv_bytes = _csv_balanca_trutest(
        [
            {
                "vid": "A001",
                "eid": "076000012345678",
                "weight": "412.5",
                "date": "2026-04-15",
            },
            {
                "eid": "076999999999999",  # sem match
                "weight": "350.0",
                "date": "2026-04-15",
            },
        ],
    )
    r = client.post(
        "/pesagens/importar-csv",
        files={"arquivo": ("peso.csv", csv_bytes, "text/csv")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["importadas"] == 1
    assert body["pareadas"] == 1
    assert len(body["erros"]) == 1
    assert "nenhum animal" in body["erros"][0]["motivo"]

    r = client.get(f"/pesagens?animal_id={animal_com_eid['id']}")
    assert r.status_code == 200 and len(r.json()) == 1


def test_importar_csv_balanca_match_via_vid(client: TestClient, animal_com_eid) -> None:
    csv_bytes = _csv_balanca_trutest(
        [
            # Sem EID; match deve cair no VID -> Animal.brinco=A001
            {"vid": "A001", "weight": "415.0", "date": "2026-05-01"},
        ],
    )
    r = client.post(
        "/pesagens/importar-csv",
        files={"arquivo": ("peso.csv", csv_bytes, "text/csv")},
    )
    body = r.json()
    assert body["importadas"] == 1
    assert body["pareadas"] == 1


def test_csv_balanca_rejeita_peso_zero(client: TestClient, animal_com_eid) -> None:
    csv_bytes = b"VID,Weight,Date\nA001,0,2026-04-15\n"
    r = client.post(
        "/pesagens/importar-csv",
        files={"arquivo": ("peso.csv", csv_bytes, "text/csv")},
    )
    body = r.json()
    assert body["importadas"] == 0
    assert any("nao-positivo" in e["motivo"] for e in body["erros"])


def test_csv_balanca_rejeita_sem_peso(client: TestClient) -> None:
    csv_bytes = b"VID,Date\nA001,2026-04-15\n"
    r = client.post(
        "/pesagens/importar-csv",
        files={"arquivo": ("peso.csv", csv_bytes, "text/csv")},
    )
    body = r.json()
    assert body["importadas"] == 0
    assert any("peso" in e["motivo"].lower() for e in body["erros"])
