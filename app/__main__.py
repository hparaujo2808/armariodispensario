"""Sobe tudo com um comando:

    python -m app            Arduino Mega na USB, webcams 0 e 1
    python -m app --sim      sem hardware: Mega e câmeras simulados (demonstração e testes)

Opções: --config arquivo.json, --semear SENHA_ADMIN (refaz a carga inicial), --sem-navegador.
Na primeira vez, o banco é criado com a carga de demonstração (app/semente.py).
"""
from __future__ import annotations

import argparse
import logging
import os
import threading
import time
import webbrowser

import uvicorn

from .api import criar_app
from .config import Config
from .core import Dispensario
from .hal import criar_mega
from .mv_client import ClienteMV
from .storage import Banco, carregar_segredo

SENHA_ADMIN_INICIAL = "admin2026"
log = logging.getLogger("app")


def subir_mv_simulado(porta: int = 8090) -> str:
    """Sem MV real (o hospital ainda não liberou a API), sobe o simulador junto."""
    from .mock_mv import app as mv_app
    servidor = uvicorn.Server(uvicorn.Config(mv_app, host="127.0.0.1", port=porta, log_level="warning"))
    threading.Thread(target=servidor.run, daemon=True, name="mv-simulado").start()
    for _ in range(50):
        if servidor.started:
            break
        time.sleep(0.1)
    return f"http://127.0.0.1:{porta}"


def montar(cfg: Config, semear_senha: str = "") -> Dispensario:
    os.makedirs(cfg.dados_dir, exist_ok=True)
    banco = Banco(os.path.join(cfg.dados_dir, "dispensario.db"), carregar_segredo(cfg.caminho_segredo))
    mega = criar_mega(cfg)
    if semear_senha or not banco.usuarios():
        from .semente import semear
        semear(banco, semear_senha or SENHA_ADMIN_INICIAL, mega)
        if not semear_senha:
            log.warning("banco novo: painel com usuário 'admin' e senha '%s' — TROQUE", SENHA_ADMIN_INICIAL)
    url = cfg.mv_url or subir_mv_simulado()
    mv = ClienteMV(url, cfg.mv_token, cfg.mv_timeout_s)
    disp = Dispensario(cfg, mega, banco, mv)
    if mega.online:
        mega.ajustar(sp=int(round(cfg.setpoint_c * 10)), alarme=cfg.alarme_porta_s)
    return disp


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m app")
    ap.add_argument("--config")
    ap.add_argument("--sim", action="store_true", help="Mega e câmeras simulados (sem hardware)")
    ap.add_argument("--semear", metavar="SENHA_ADMIN", default="", help="refaz a carga inicial com esta senha de admin")
    ap.add_argument("--sem-navegador", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = Config.carregar(a.config)
    if a.sim:
        cfg.porta_serial = "sim"
        cfg.cameras = [{"nome": "externa", "fonte": "sim"}, {"nome": "interna", "fonte": "sim"}]
        cfg.dados_dir = cfg.dados_dir if cfg.dados_dir != "dados" else "dados_sim"
    disp = montar(cfg, a.semear)
    base = f"http://{cfg.api_host}:{cfg.api_porta}"
    print(f"\nQuiosque: {base}/   ·   Painel: {base}/painel   ·   MV simulado: http://127.0.0.1:8090/docs\n")
    if not a.sem_navegador:
        threading.Timer(1.5, lambda: (webbrowser.open(base + "/"), webbrowser.open(base + "/painel"))).start()
    uvicorn.run(criar_app(disp), host=cfg.api_host, port=cfg.api_porta, log_level="warning")


if __name__ == "__main__":
    main()
