from fastapi import FastAPI

from app.routers import (
    animais,
    aplicacoes_sanitarias,
    atendimentos_veterinarios,
    avaliacoes,
    campanhas,
    dispositivos,
    fazendas,
    identificacoes,
    lotes,
    pesagens,
)

app = FastAPI(
    title="IndexBeef API",
    version="0.1.0",
    description="Avaliação morfológica de bovinos Nelore por visão computacional.",
)

app.include_router(fazendas.router)
app.include_router(lotes.router)
app.include_router(animais.router)
app.include_router(pesagens.router)
app.include_router(identificacoes.router)
app.include_router(dispositivos.router)
app.include_router(campanhas.router)
app.include_router(aplicacoes_sanitarias.router)
app.include_router(atendimentos_veterinarios.router)
app.include_router(avaliacoes.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "indexbeef-api", "versao": "0.1.0"}
