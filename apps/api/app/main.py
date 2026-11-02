from fastapi import FastAPI

from app.routers import avaliacoes

app = FastAPI(
    title="IndexBeef API",
    version="0.1.0",
    description="Avaliação morfológica de bovinos Nelore por visão computacional.",
)

app.include_router(avaliacoes.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "indexbeef-api", "versao": "0.1.0"}
