"""Testes da Fase 5 — auth JWT, sincronizacao fazenda<->nuvem, painel remoto,
verificacao de atualizacao de modelos.

Cobre (minimo 15):
1.  POST /auth/registrar: 201 com email unico
2.  POST /auth/registrar: 409 se email duplicado
3.  POST /auth/login: 200 com token
4.  POST /auth/login: 401 com senha errada
5.  GET /auth/me: 200 com token valido
6.  GET /auth/me: 401 sem token
7.  GET /auth/me: 401 com token invalido
8.  POST /sync/push: processa animal + pesagem; processados=2
9.  POST /sync/push: tabela invalida retorna 422
10. GET /sync/pull: registros de animal modificados desde data futura -> lista vazia
11. GET /sync/pull: animais modificados recentemente -> retorna
12. GET /fazendas/{id}/painel-remoto: 200 com fazenda existente
13. GET /fazendas/{id}/painel-remoto: estrutura correta
14. GET /fazendas/{id}/painel-remoto: 404 para fazenda inexistente
15. GET /modelo_versao/verificar-atualizacao: atualizar=false se nao ha versao ativa
16. GET /modelo_versao/verificar-atualizacao: atualizar=true se ha nova versao ativa
17. GET /modelo_versao/verificar-atualizacao: atualizar=false se versao_atual coincide com ativa
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
from app.models.enums import CategoriaLote, OrigemPesagem, Sexo
from app.models.lote import Lote
from app.models.modelo_versao import ModeloVersao
from app.models.pesagem import Pesagem

# ---------------------------------------------------------------------------
# Fixtures (padrao identico ao test_fase4.py)
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
def setup_fazenda_animal(db_engine):
    """Cria fazenda, lote, animal e pesagem basicos."""
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    with SessionLocal() as s:
        fazenda = Fazenda(nome="Fazenda Fase5", bioma="Pantanal", municipio="Corumba", uf="MS")
        s.add(fazenda)
        s.flush()

        lote = Lote(fazenda_id=fazenda.id, nome="Lote B", categoria=CategoriaLote.garrote)
        s.add(lote)
        s.flush()

        animal = Animal(
            fazenda_id=fazenda.id,
            lote_id=lote.id,
            sexo=Sexo.M,
            brinco="F5-001",
            nascimento=date(2025, 1, 1),
        )
        s.add(animal)
        s.flush()

        pesagem = Pesagem(
            animal_id=animal.id,
            data=date(2026, 11, 1),
            peso_kg=350.0,
            origem=OrigemPesagem.balanca,
        )
        s.add(pesagem)
        s.commit()
        s.refresh(fazenda)
        s.refresh(lote)
        s.refresh(animal)
        return fazenda, lote, animal


# ---------------------------------------------------------------------------
# 1. POST /auth/registrar: 201 com email unico
# ---------------------------------------------------------------------------


def test_registrar_usuario_201(client: TestClient) -> None:
    r = client.post("/auth/registrar", json={
        "email": "criador@fazenda.com",
        "nome": "Joao Criador",
        "senha": "s3nh@segura",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "criador@fazenda.com"
    assert body["nome"] == "Joao Criador"
    assert "id" in body
    assert "senha" not in body
    assert "senha_hash" not in body


# ---------------------------------------------------------------------------
# 2. POST /auth/registrar: 409 se email duplicado
# ---------------------------------------------------------------------------


def test_registrar_email_duplicado_409(client: TestClient) -> None:
    payload = {"email": "dup@teste.com", "nome": "Dup", "senha": "abc123"}
    client.post("/auth/registrar", json=payload)
    r = client.post("/auth/registrar", json=payload)
    assert r.status_code == 409, r.text


# ---------------------------------------------------------------------------
# 3. POST /auth/login: 200 com token
# ---------------------------------------------------------------------------


def test_login_200_com_token(client: TestClient) -> None:
    client.post("/auth/registrar", json={
        "email": "login@teste.com",
        "nome": "Login User",
        "senha": "minhasenha",
    })
    r = client.post("/auth/login", json={"email": "login@teste.com", "senha": "minhasenha"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


# ---------------------------------------------------------------------------
# 4. POST /auth/login: 401 com senha errada
# ---------------------------------------------------------------------------


def test_login_401_senha_errada(client: TestClient) -> None:
    client.post("/auth/registrar", json={
        "email": "wrong@teste.com",
        "nome": "Wrong",
        "senha": "certa",
    })
    r = client.post("/auth/login", json={"email": "wrong@teste.com", "senha": "errada"})
    assert r.status_code == 401, r.text


# ---------------------------------------------------------------------------
# 5. GET /auth/me: 200 com token valido
# ---------------------------------------------------------------------------


def test_me_200_com_token(client: TestClient) -> None:
    client.post("/auth/registrar", json={
        "email": "me@teste.com",
        "nome": "Me User",
        "senha": "pass123",
    })
    login_r = client.post("/auth/login", json={"email": "me@teste.com", "senha": "pass123"})
    token = login_r.json()["access_token"]

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "me@teste.com"


# ---------------------------------------------------------------------------
# 6. GET /auth/me: 401 sem token
# ---------------------------------------------------------------------------


def test_me_401_sem_token(client: TestClient) -> None:
    r = client.get("/auth/me")
    assert r.status_code == 401, r.text


# ---------------------------------------------------------------------------
# 7. GET /auth/me: 401 com token invalido
# ---------------------------------------------------------------------------


def test_me_401_token_invalido(client: TestClient) -> None:
    r = client.get("/auth/me", headers={"Authorization": "Bearer token.invalido.aqui"})
    assert r.status_code == 401, r.text


# ---------------------------------------------------------------------------
# 8. POST /sync/push: processa animal + pesagem; processados=2
# ---------------------------------------------------------------------------


def test_sync_push_animal_e_pesagem(client: TestClient, setup_fazenda_animal: tuple) -> None:
    fazenda, lote, animal = setup_fazenda_animal
    novo_animal_id = str(uuid.uuid4())
    nova_pesagem_id = str(uuid.uuid4())

    r = client.post("/sync/push", json={
        "estacao_id": "tablet-001",
        "registros": [
            {
                "tabela": "animal",
                "dados": {
                    "id": novo_animal_id,
                    "fazenda_id": str(fazenda.id),
                    "lote_id": str(lote.id),
                    "brinco": "SYNC-001",
                    "sexo": "M",
                    "raca": "Nelore",
                    "situacao": "ativo",
                    "ceip": False,
                    "atualizado_em": datetime.now(UTC).isoformat(),
                },
            },
            {
                "tabela": "pesagem",
                "dados": {
                    "id": nova_pesagem_id,
                    "animal_id": novo_animal_id,
                    "data": "2026-11-03",
                    "peso_kg": "420.00",
                    "origem": "balanca",
                    "atualizado_em": datetime.now(UTC).isoformat(),
                },
            },
        ],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["erros"] == [], f"Erros: {body['erros']}"
    assert body["processados"] == 2
    assert "sincronizado_em" in body


# ---------------------------------------------------------------------------
# 9. POST /sync/push: tabela invalida retorna 422
# ---------------------------------------------------------------------------


def test_sync_push_tabela_invalida_422(client: TestClient) -> None:
    r = client.post("/sync/push", json={
        "estacao_id": "tablet-001",
        "registros": [
            {"tabela": "nao_existe", "dados": {"id": str(uuid.uuid4())}},
        ],
    })
    assert r.status_code == 422, r.text


# ---------------------------------------------------------------------------
# 10. GET /sync/pull: data futura -> lista vazia
# ---------------------------------------------------------------------------


def test_sync_pull_data_futura_lista_vazia(client: TestClient) -> None:
    # Usar formato sem timezone (Z) para evitar problemas de codificacao na URL
    futuro = (datetime.now(UTC) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
    r = client.get(f"/sync/pull?estacao_id=tablet-001&desde={futuro}&tabelas=animal")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 0
    assert body["registros"] == []


# ---------------------------------------------------------------------------
# 11. GET /sync/pull: animais modificados recentemente -> retorna
# ---------------------------------------------------------------------------


def test_sync_pull_retorna_animais_recentes(
    client: TestClient, setup_fazenda_animal: tuple,
) -> None:
    # Animal foi criado ha pouco, buscar desde 1 hora atras deve retornar
    desde = (datetime.now(UTC) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    r = client.get(f"/sync/pull?estacao_id=tablet-001&desde={desde}&tabelas=animal")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 1
    tabelas = [reg["tabela"] for reg in body["registros"]]
    assert "animal" in tabelas


# ---------------------------------------------------------------------------
# 12. GET /fazendas/{id}/painel-remoto: 200 com fazenda existente
# ---------------------------------------------------------------------------


def test_painel_remoto_200(client: TestClient, setup_fazenda_animal: tuple) -> None:
    fazenda, _, _ = setup_fazenda_animal
    r = client.get(f"/fazendas/{fazenda.id}/painel-remoto")
    assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# 13. GET /fazendas/{id}/painel-remoto: estrutura correta
# ---------------------------------------------------------------------------


def test_painel_remoto_estrutura(client: TestClient, setup_fazenda_animal: tuple) -> None:
    fazenda, _, _ = setup_fazenda_animal
    r = client.get(f"/fazendas/{fazenda.id}/painel-remoto")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "fazenda" in body
    assert "totais" in body
    assert "ultimas_avaliacoes" in body
    assert "alertas_ecc" in body
    assert "peso_medio_lote" in body
    assert body["totais"]["animais"] >= 1
    assert body["fazenda"]["nome"] == "Fazenda Fase5"
    assert body["fazenda"]["municipio"] == "Corumba"
    assert body["fazenda"]["uf"] == "MS"


# ---------------------------------------------------------------------------
# 14. GET /fazendas/{id}/painel-remoto: 404 para fazenda inexistente
# ---------------------------------------------------------------------------


def test_painel_remoto_404(client: TestClient) -> None:
    r = client.get(f"/fazendas/{uuid.uuid4()}/painel-remoto")
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# 15. GET /modelo_versao/verificar-atualizacao: atualizar=false sem versao ativa
# ---------------------------------------------------------------------------


def test_verificar_atualizacao_false_sem_versao(client: TestClient) -> None:
    r = client.get("/modelos-versao/verificar-atualizacao?nome=segmentacao&versao_atual=0.1.0")
    assert r.status_code == 200, r.text
    assert r.json()["atualizar"] is False


# ---------------------------------------------------------------------------
# 16. GET /modelo_versao/verificar-atualizacao: atualizar=true se nova versao ativa
# ---------------------------------------------------------------------------


def test_verificar_atualizacao_true_nova_versao(client: TestClient) -> None:
    # Registrar modelo ativo com versao diferente
    client.post("/modelos-versao", json={
        "nome": "keypoints_lateral",
        "versao": "1.2.0",
        "ativo": True,
        "artefato_url": "http://minio/modelos/keypoints_lateral_1.2.0.onnx",
        "metricas": {"PCK": 0.87},
    })
    r = client.get(
        "/modelos-versao/verificar-atualizacao?nome=keypoints_lateral&versao_atual=0.0.0",
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["atualizar"] is True
    assert body["versao"] == "1.2.0"
    assert "artefato_url" in body
    assert "metricas" in body


# ---------------------------------------------------------------------------
# 17. GET /modelo_versao/verificar-atualizacao: atualizar=false se versao coincide
# ---------------------------------------------------------------------------


def test_verificar_atualizacao_false_versao_igual(client: TestClient) -> None:
    client.post("/modelos-versao", json={
        "nome": "peso",
        "versao": "2.0.0",
        "ativo": True,
    })
    r = client.get(
        "/modelos-versao/verificar-atualizacao?nome=peso&versao_atual=2.0.0",
    )
    assert r.status_code == 200, r.text
    assert r.json()["atualizar"] is False
