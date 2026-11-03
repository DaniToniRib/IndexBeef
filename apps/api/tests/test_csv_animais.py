"""Testes do servico de importacao CSV de animais."""

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
from app.services.csv_animais import parse_csv_animais

_FAZENDA_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# --- Testes unitarios do parser ---


def test_parse_csv_basico() -> None:
    csv = "brinco,sexo\n1234,M\n5678,F\n"
    linhas, erros = parse_csv_animais(csv, _FAZENDA_ID)
    assert erros == []
    assert len(linhas) == 2
    assert linhas[0]["brinco"] == "1234"
    assert linhas[0]["sexo"] == "M"
    assert linhas[0]["raca"] == "Nelore"
    assert linhas[1]["sexo"] == "F"


def test_parse_csv_campos_opcionais() -> None:
    csv = "brinco,sexo,nascimento,ceip,variedade\n001,M,2024-01-15,sim,mocho\n"
    linhas, erros = parse_csv_animais(csv, _FAZENDA_ID)
    assert erros == []
    lin = linhas[0]
    assert lin["nascimento"] == date(2024, 1, 15)
    assert lin["ceip"] is True
    assert lin["variedade"] == "mocho"


def test_parse_csv_data_formato_ptbr() -> None:
    csv = "brinco,sexo,nascimento\n001,M,15/01/2024\n"
    linhas, erros = parse_csv_animais(csv, _FAZENDA_ID)
    assert erros == []
    assert linhas[0]["nascimento"] == date(2024, 1, 15)


def test_parse_csv_sexo_invalido_vira_erro() -> None:
    csv = "brinco,sexo\n001,X\n"
    linhas, erros = parse_csv_animais(csv, _FAZENDA_ID)
    assert linhas == []
    assert len(erros) == 1
    assert erros[0]["linha"] == "2"


def test_parse_csv_sem_coluna_sexo_retorna_erro_cabecalho() -> None:
    csv = "brinco,nascimento\n001,2024-01-01\n"
    linhas, erros = parse_csv_animais(csv, _FAZENDA_ID)
    assert linhas == []
    assert any("sexo" in e["motivo"] for e in erros)


def test_parse_csv_variedade_invalida_ignorada() -> None:
    csv = "brinco,sexo,variedade\n001,M,invalido\n"
    linhas, erros = parse_csv_animais(csv, _FAZENDA_ID)
    assert erros == []
    assert linhas[0]["variedade"] is None


def test_parse_csv_mistura_validos_e_invalidos() -> None:
    csv = "brinco,sexo,nascimento\n001,M,2024-01-01\n002,Z,2024-01-01\n003,F,\n"
    linhas, erros = parse_csv_animais(csv, _FAZENDA_ID)
    assert len(linhas) == 2  # 001 e 003
    assert len(erros) == 1
    assert erros[0]["linha"] == "3"


# --- Testes de integracao do endpoint ---


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
def fazenda_id(client: TestClient) -> str:
    r = client.post("/fazendas", json={"nome": "Fazenda Teste", "bioma": "Pantanal"})
    assert r.status_code == 201
    return r.json()["id"]


def test_importar_csv_via_endpoint(client: TestClient, fazenda_id: str) -> None:
    csv_conteudo = "brinco,sexo\n1111,M\n2222,F\n"
    r = client.post(
        f"/animais/importar-csv?fazenda_id={fazenda_id}",
        files={"arquivo": ("animais.csv", csv_conteudo.encode(), "text/csv")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["importadas"] == 2
    assert body["erros"] == []

    r2 = client.get(f"/animais?fazenda_id={fazenda_id}")
    assert r2.status_code == 200
    brincos = [a["brinco"] for a in r2.json()]
    assert "1111" in brincos
    assert "2222" in brincos


def test_importar_csv_com_erros_parciais(client: TestClient, fazenda_id: str) -> None:
    csv_conteudo = "brinco,sexo\n3333,M\n4444,X\n"
    r = client.post(
        f"/animais/importar-csv?fazenda_id={fazenda_id}",
        files={"arquivo": ("animais.csv", csv_conteudo.encode(), "text/csv")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["importadas"] == 1
    assert len(body["erros"]) == 1
