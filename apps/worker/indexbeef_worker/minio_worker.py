"""Cliente MinIO para o worker (sem dependencia do pacote app/)."""

from __future__ import annotations

import os
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


def _s3():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "indexbeef"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "indexbeef"),
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


_BUCKET = os.getenv("MINIO_BUCKET", "indexbeef")


def _garantir_bucket(s3) -> None:
    try:
        s3.head_bucket(Bucket=_BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=_BUCKET)


def upload_bytes(data: bytes, content_type: str, extensao: str = "bin") -> str:
    s3 = _s3()
    _garantir_bucket(s3)
    chave = f"{uuid.uuid4()}.{extensao}"
    s3.put_object(Bucket=_BUCKET, Key=chave, Body=data, ContentType=content_type)
    endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    return f"{endpoint}/{_BUCKET}/{chave}"


def download_bytes(url: str) -> bytes:
    partes = url.split("/", 4)
    if len(partes) < 5:
        raise ValueError(f"URL MinIO invalida: {url}")
    bucket = partes[3]
    chave = partes[4]
    s3 = _s3()
    resp = s3.get_object(Bucket=bucket, Key=chave)
    return resp["Body"].read()
