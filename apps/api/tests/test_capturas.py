"""Testes dos endpoints /capturas."""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import get_db
from app.main import app
from app.models import Base
from app.models.avaliacao import Avaliacao
from app.models.enums import StatusAvaliacao

_JPEG_MINIMO = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
    b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e\x00"
    b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f"
    b"\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01"
    b"\x00\x00?\x00\xfb\xff\xd9"
)


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


def test_extrair_frame_foto_retorna_url(client: TestClient) -> None:
    fake_url = "http://minio:9000/indexbeef/foto.jpg"
    with (
        patch("app.routers.capturas.minio_disponivel", return_value=True),
        patch("app.routers.capturas.upload_bytes", return_value=fake_url),
    ):
        r = client.post(
            "/capturas/extrair-frame",
            files={"arquivo": ("foto.jpg", io.BytesIO(_JPEG_MINIMO), "image/jpeg")},
        )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["frame_url"] == fake_url
    assert body["tipo_mime"] == "image/jpeg"


def test_extrair_frame_sem_minio_retorna_503(client: TestClient) -> None:
    with patch("app.routers.capturas.minio_disponivel", return_value=False):
        r = client.post(
            "/capturas/extrair-frame",
            files={"arquivo": ("foto.jpg", io.BytesIO(_JPEG_MINIMO), "image/jpeg")},
        )
    assert r.status_code == 503


def test_extrair_frame_tipo_invalido_retorna_415(client: TestClient) -> None:
    with patch("app.routers.capturas.minio_disponivel", return_value=True):
        r = client.post(
            "/capturas/extrair-frame",
            files={"arquivo": ("doc.pdf", io.BytesIO(b"PDF"), "application/pdf")},
        )
    assert r.status_code == 415


# ---------------------------------------------------------------------------
# POST /capturas
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def _avaliacao(session) -> Avaliacao:
    av = Avaliacao(
        animal_id=uuid.uuid4(),
        data_hora=datetime.now(tz=timezone.utc),
        status=StatusAvaliacao.processando,
    )
    session.add(av)
    session.commit()
    session.refresh(av)
    return av


def test_criar_captura_foto_retorna_201(client: TestClient, db_session) -> None:
    av = _avaliacao(db_session)
    r = client.post("/capturas", json={
        "avaliacao_id": str(av.id),
        "arquivo_url": "http://minio:9000/indexbeef/foto.jpg",
        "tipo": "foto",
        "vista": "lateral",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["avaliacao_id"] == str(av.id)
    assert body["arquivo_url"] == "http://minio:9000/indexbeef/foto.jpg"
    assert body["tipo"] == "foto"
    assert body["vista"] == "lateral"


def test_criar_captura_avaliacao_inexistente_retorna_404(client: TestClient) -> None:
    r = client.post("/capturas", json={
        "avaliacao_id": str(uuid.uuid4()),
        "arquivo_url": "http://minio:9000/indexbeef/foto.jpg",
    })
    assert r.status_code == 404
