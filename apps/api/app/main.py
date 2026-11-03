from fastapi import FastAPI

from app.routers import (
    animais,
    aplicacoes_sanitarias,
    atendimentos_veterinarios,
    avaliacoes,
    campanhas,
    capturas,
    dashboard,
    dispositivos,
    eventos_reprodutivos,
    exames_andrologicos,
    fazendas,
    gps,
    identificacoes,
    indices,
    leituras_rfid,
    lotes,
    modelo_versao,
    pesagens,
    relatorio,
    relatorios,
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
app.include_router(leituras_rfid.router)
app.include_router(campanhas.router)
app.include_router(aplicacoes_sanitarias.router)
app.include_router(atendimentos_veterinarios.router)
app.include_router(gps.router)
app.include_router(avaliacoes.router)
app.include_router(capturas.router)
app.include_router(dashboard.router)
app.include_router(relatorios.router)
app.include_router(relatorio.router)
app.include_router(modelo_versao.router)
app.include_router(eventos_reprodutivos.router)
app.include_router(exames_andrologicos.router)
app.include_router(indices.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "indexbeef-api", "versao": "0.1.0"}
