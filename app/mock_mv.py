"""Simulador do sistema MV/RMV para desenvolvimento e validação (Risco 2).

Implementa o mesmo contrato do adaptador `mv_client.ClienteMV`:
  GET  /prescricoes?identificador=...
  POST /dispensacoes
Execução:  python -m dispensario.mock_mv  (porta 8090)
"""
from __future__ import annotations

from typing import Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

# CPFs fictícios (gerados apenas para teste; não pertencem a pessoas reais)
PRESCRICOES: Dict[str, dict] = {
    "11122233344": {
        "prescricao_id": "RX-2026-000101",
        "paciente": {"nome": "Paciente Teste A", "leito": "305-A"},
        "itens": [
            {"codigo": "INS-NPH", "descricao": "Insulina NPH 100 UI/mL (frasco 10 mL)", "quantidade": 1, "posologia": "10 UI SC 7h"},
            {"codigo": "SER-1ML", "descricao": "Seringa de insulina 1 mL c/ agulha", "quantidade": 2, "posologia": ""},
        ],
    },
    "55566677788": {
        "prescricao_id": "RX-2026-000102",
        "paciente": {"nome": "Paciente Teste B", "leito": "307-B"},
        "itens": [
            {"codigo": "FRA-G", "descricao": "Fralda geriátrica G", "quantidade": 4, "posologia": ""},
            {"codigo": "GAZ-10", "descricao": "Compressa de gaze 7,5x7,5 (pct 10)", "quantidade": 2, "posologia": ""},
            {"codigo": "ATA-10", "descricao": "Atadura de crepe 10 cm", "quantidade": 1, "posologia": ""},
        ],
    },
    "RX000103": {
        "prescricao_id": "RX-2026-000103",
        "paciente": {"nome": "Paciente Teste C", "leito": "310-A"},
        "itens": [
            {"codigo": "SF-10", "descricao": "Soro fisiológico 0,9% 10 mL (ampola)", "quantidade": 3, "posologia": "flush"},
            {"codigo": "SER-10", "descricao": "Seringa 10 mL", "quantidade": 3, "posologia": ""},
        ],
    },
}


def criar_mock() -> FastAPI:
    app = FastAPI(title="MV/RMV — simulador")
    recebidas: List[dict] = []
    vistos = set()

    @app.get("/prescricoes")
    def prescricoes(identificador: str = Query(...)):
        chave = "".join(c for c in identificador.upper() if c.isalnum())
        if chave not in PRESCRICOES:
            raise HTTPException(404, "sem prescrição ativa")
        return PRESCRICOES[chave]

    @app.post("/dispensacoes")
    def dispensacoes(d: dict):
        if d.get("sessao_id") in vistos:
            return JSONResponse({"status": "duplicada"}, status_code=409)
        vistos.add(d.get("sessao_id"))
        recebidas.append(d)
        return JSONResponse({"status": "recebida"}, status_code=201)

    @app.get("/dispensacoes")
    def listar():
        return recebidas

    return app


app = criar_mock()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8090)
