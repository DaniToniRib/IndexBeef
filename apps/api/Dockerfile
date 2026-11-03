FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# OpenCV headless precisa de libGL mesmo na API (fallback sincrono de extração de frames)
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala o worker (indexbeef_vision é importado pela API no path síncrono)
COPY apps/worker/ /worker/
RUN pip install --upgrade pip && pip install /worker

# Instala a API
COPY apps/api/pyproject.toml ./
RUN pip install .

COPY apps/api/ .

EXPOSE 8000

# Aplica migrations antes de subir o servidor
CMD ["bash", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
