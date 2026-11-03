"""Testes dos endpoints sanitarios da Fase C."""

from __future__ import annotations

import uuid
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
def animal_fazenda(client: TestClient) -> tuple[str, str]:
    f = client.post(
        "/fazendas", json={"nome": "Teste", "tipo": "fazenda"},
    ).json()
    a = client.post(
        "/animais",
        json={"fazenda_id": f["id"], "sexo": "F", "nascimento": "2024-01-01"},
    ).json()
    return f["id"], a["id"]


# ------- Campanha -------

def test_campanha_crud(client: TestClient, animal_fazenda) -> None:
    fid, _ = animal_fazenda
    r = client.post(
        "/campanhas",
        json={
            "fazenda_id": fid,
            "nome": "Brucelose 2026",
            "tipo": "vacina",
            "data_inicio": "2026-04-01",
        },
    )
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    assert r.json()["status"] == "planejada"

    r = client.patch(f"/campanhas/{cid}", json={"status": "em_andamento"})
    assert r.status_code == 200 and r.json()["status"] == "em_andamento"


# ------- Aplicacao sanitaria -------

def test_aplicacao_vacina_exige_crmv(client: TestClient, animal_fazenda) -> None:
    _, aid = animal_fazenda
    r = client.post(
        "/aplicacoes-sanitarias",
        json={
            "animal_id": aid,
            "tipo": "vacina",
            "data": "2026-04-15",
            "principio_ativo": "Brucella abortus B19",
            "via": "SC",
            # sem CRMV!
        },
    )
    assert r.status_code == 422
    assert "veterinario_crmv" in r.text.lower()


def test_aplicacao_vermifugo_dispensa_crmv(client: TestClient, animal_fazenda) -> None:
    _, aid = animal_fazenda
    r = client.post(
        "/aplicacoes-sanitarias",
        json={
            "animal_id": aid,
            "tipo": "vermifugo",
            "data": "2026-04-15",
            "principio_ativo": "Ivermectina 1%",
            "dose_ml": "20",
            "via": "SC",
            "carencia_abate_dias": 35,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    # apto_abate_em = 2026-04-15 + 35d = 2026-05-20
    assert body["apto_abate_em"] == "2026-05-20"


def test_aplicacao_vacina_com_crmv_valido(client: TestClient, animal_fazenda) -> None:
    _, aid = animal_fazenda
    r = client.post(
        "/aplicacoes-sanitarias",
        json={
            "animal_id": aid,
            "tipo": "vacina",
            "data": "2026-04-15",
            "principio_ativo": "Brucella abortus B19",
            "via": "SC",
            "veterinario_crmv": "MS-98765",
            "veterinario_nome": "Dra. Souza",
            "lote_medicamento": "LOT-2026-01",
            "validade": "2027-12-31",
        },
    )
    assert r.status_code == 201, r.text


def test_aplicacao_crmv_formato_invalido(client: TestClient, animal_fazenda) -> None:
    _, aid = animal_fazenda
    r = client.post(
        "/aplicacoes-sanitarias",
        json={
            "animal_id": aid,
            "tipo": "vacina",
            "data": "2026-04-15",
            "principio_ativo": "x",
            "via": "SC",
            "veterinario_crmv": "123",  # invalido
        },
    )
    assert r.status_code == 422


def test_aplicacao_rejeita_validade_passada(client: TestClient, animal_fazenda) -> None:
    _, aid = animal_fazenda
    r = client.post(
        "/aplicacoes-sanitarias",
        json={
            "animal_id": aid,
            "tipo": "vermifugo",
            "data": "2026-04-15",
            "principio_ativo": "Ivermectina 1%",
            "via": "SC",
            "validade": "2025-01-01",
        },
    )
    assert r.status_code == 422
    assert "vencido" in r.text.lower()


def test_aplicacoes_lista_filtra_por_animal(client: TestClient, animal_fazenda) -> None:
    _, aid = animal_fazenda
    client.post(
        "/aplicacoes-sanitarias",
        json={
            "animal_id": aid,
            "tipo": "vermifugo",
            "data": "2026-04-15",
            "principio_ativo": "Ivermectina 1%",
            "via": "SC",
        },
    )
    client.post(
        "/aplicacoes-sanitarias",
        json={
            "animal_id": aid,
            "tipo": "vermifugo",
            "data": "2026-10-15",
            "principio_ativo": "Moxidectina",
            "via": "SC",
        },
    )
    r = client.get(f"/aplicacoes-sanitarias?animal_id={aid}")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    # Ordem desc
    assert body[0]["data"] == "2026-10-15"


# ------- Atendimento veterinario -------

def test_atendimento_vet_crud_com_crmv(client: TestClient, animal_fazenda) -> None:
    _, aid = animal_fazenda
    r = client.post(
        "/atendimentos-veterinarios",
        json={
            "animal_id": aid,
            "data_hora": datetime.now(UTC).isoformat(),
            "veterinario_nome": "Dr. Nunes",
            "veterinario_crmv": "SP-12345",
            "motivo": "profilático",
            "temperatura_c": "38.5",
            "frequencia_cardiaca": 72,
            "diagnostico": "animal clinicamente saudavel",
            "prescricoes": [
                {
                    "principio_ativo": "oxitetraciclina LA",
                    "dose_mg_por_kg": 20,
                    "via": "IM",
                    "duracao_dias": 3,
                    "carencia_abate_dias": 28,
                },
            ],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["veterinario_crmv"] == "SP-12345"
    assert body["prescricoes"][0]["duracao_dias"] == 3


def test_atendimento_crmv_obrigatorio(client: TestClient, animal_fazenda) -> None:
    _, aid = animal_fazenda
    r = client.post(
        "/atendimentos-veterinarios",
        json={
            "animal_id": aid,
            "data_hora": datetime.now(UTC).isoformat(),
            "veterinario_nome": "x",
            "motivo": "y",
            # sem crmv
        },
    )
    assert r.status_code == 422


def test_atendimento_crmv_formato_invalido(client: TestClient, animal_fazenda) -> None:
    _, aid = animal_fazenda
    r = client.post(
        "/atendimentos-veterinarios",
        json={
            "animal_id": aid,
            "data_hora": datetime.now(UTC).isoformat(),
            "veterinario_nome": "x",
            "veterinario_crmv": "SP12",  # invalido (muito curto)
            "motivo": "y",
        },
    )
    assert r.status_code == 422


def test_atendimentos_lista_por_animal(client: TestClient, animal_fazenda) -> None:
    _, aid = animal_fazenda
    client.post(
        "/atendimentos-veterinarios",
        json={
            "animal_id": aid,
            "data_hora": datetime(2026, 5, 1, 10, tzinfo=UTC).isoformat(),
            "veterinario_nome": "x",
            "veterinario_crmv": "SP-12345",
            "motivo": "a",
        },
    )
    client.post(
        "/atendimentos-veterinarios",
        json={
            "animal_id": aid,
            "data_hora": datetime(2026, 6, 1, 10, tzinfo=UTC).isoformat(),
            "veterinario_nome": "y",
            "veterinario_crmv": "SP-54321",
            "motivo": "b",
        },
    )
    r = client.get(f"/atendimentos-veterinarios?animal_id={aid}")
    assert r.status_code == 200 and len(r.json()) == 2


def test_atendimento_404(client: TestClient) -> None:
    r = client.get(f"/atendimentos-veterinarios/{uuid.uuid4()}")
    assert r.status_code == 404
