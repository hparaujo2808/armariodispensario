"""API HTTP do dispensário (FastAPI).

/api/kiosk/*  -> tela do quiosque (só aceita conexões da própria máquina)
/api/kiosk/sim/* -> botões de simulação (só com o Mega simulado)
/api/*        -> painel da farmácia/logística/TI (token Bearer + perfil)  RF06, RF08, RF10, RF11, RF13
/             -> tela do quiosque (web/kiosk.html, no navegador do notebook em tela cheia)
/painel       -> painel web (web/painel.html)
"""
from __future__ import annotations

import asyncio
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from . import auth as A
from .core import Dispensario, ErroOperacao
from .storage import ErroRegra

log = logging.getLogger(__name__)
WEB = os.path.join(os.path.dirname(__file__), "web")
LOCAIS = {"127.0.0.1", "::1", "localhost", "testclient"}


# ------------------------------------------------------------------ modelos
class Login(BaseModel):
    matricula: str
    senha: str


class Consulta(BaseModel):
    identificador: str


class SimAuth(BaseModel):
    mega_id: int
    metodo: str = "digital"
    senha: Optional[str] = None


class SimPorta(BaseModel):
    aberta: bool


class SimTemp(BaseModel):
    baia: float
    cooler1: float = 38.0
    cooler2: float = 38.0


class SenhaPorta(BaseModel):
    senha: str


class Confirmacao(BaseModel):
    quantidades: Optional[Dict[str, int]] = None


class ItemContingencia(BaseModel):
    codigo: str
    quantidade: int


class Contingencia(BaseModel):
    identificador: str
    itens: List[ItemContingencia]


class ItemIn(BaseModel):
    codigo: str
    nome: str
    unidade: str = "un"
    requer_refrigeracao: bool = False
    estoque_minimo: int = 0


class CompartimentoIn(BaseModel):
    id: str
    nome: str
    climatizado: bool = False
    ordem: int = 0


class Alocacao(BaseModel):
    compartimento: str
    item: str


class Ajuste(BaseModel):
    compartimento: str
    item: str
    quantidade: int
    motivo: str


class UsuarioIn(BaseModel):
    matricula: str
    nome: str
    perfil: str
    senha: Optional[str] = None


class Ativo(BaseModel):
    ativo: bool


def criar_app(disp: Dispensario, laços: bool = True) -> FastAPI:
    tokens: Dict[str, dict] = {}

    @asynccontextmanager
    async def ciclo(app):
        tarefas = []
        if laços:
            async def laco_tick():
                while True:
                    try:
                        await asyncio.to_thread(disp.tick)
                    except Exception:  # noqa: BLE001
                        log.exception("erro no tick")
                    await asyncio.sleep(0.1)

            async def laco_lento():
                n = 0
                while True:
                    await asyncio.sleep(30)
                    n += 1
                    try:
                        await asyncio.to_thread(disp.enviar_pendentes_mv)
                        if n % 2880 == 1:   # ~1x/dia
                            await asyncio.to_thread(disp.expurgar_midia)
                    except Exception:  # noqa: BLE001
                        log.exception("erro no laço lento")

            tarefas = [asyncio.create_task(laco_tick()), asyncio.create_task(laco_lento())]
        yield
        for t in tarefas:
            t.cancel()

    app = FastAPI(title="Dispensário Eletrônico", version="1.0", lifespan=ciclo)

    # ------------------------------------------------------------ dependências
    def so_local(req: Request):
        if req.client is None or req.client.host not in LOCAIS:
            raise HTTPException(403, "endpoint exclusivo da tela local do dispensário")

    def perfil(*permitidos: str):
        def dep(authorization: str = Header("")):
            tok = authorization.removeprefix("Bearer ").strip()
            s = tokens.get(tok)
            if not s or s["expira"] < time.time():
                raise HTTPException(401, "token inválido ou expirado")
            if s["perfil"] not in permitidos:
                raise HTTPException(403, "perfil sem permissão")
            return s
        return dep

    def executar(fn, *a, **k):
        try:
            return fn(*a, **k)
        except (ErroOperacao, ErroRegra, ValueError) as e:
            raise HTTPException(400, str(e))

    # ------------------------------------------------------------ páginas
    @app.get("/", response_class=HTMLResponse)
    def pagina_kiosk():
        return FileResponse(os.path.join(WEB, "kiosk.html"))

    @app.get("/painel", response_class=HTMLResponse)
    def pagina_painel():
        return FileResponse(os.path.join(WEB, "painel.html"))

    @app.get("/api/status")
    def status():
        return {"dispensario": disp.cfg.dispensario_id, "setor": disp.cfg.setor, "estado": disp.estado,
                "alarmes": sorted(disp.alarmes), "temperatura_frio": disp.temp.get("baia"),
                "mega_online": disp.mega.online, "energia_rede": disp.estado_publico()["energia_rede"], "hora": time.time()}

    # ------------------------------------------------------------ quiosque
    @app.get("/api/kiosk/estado", dependencies=[Depends(so_local)])
    def k_estado():
        return disp.estado_publico()

    # ------------------------------------------------------------ simulação (só com o Mega simulado)
    def so_simulado():
        if disp.cfg.porta_serial != "sim":
            raise HTTPException(404, "simulação desligada")

    @app.post("/api/kiosk/sim/autenticar", dependencies=[Depends(so_local), Depends(so_simulado)])
    def sim_auth(d: SimAuth):
        disp.mega.autenticar(d.mega_id, d.metodo, d.senha)
        disp.tick()
        return disp.estado_publico()

    @app.post("/api/kiosk/sim/porta", dependencies=[Depends(so_local), Depends(so_simulado)])
    def sim_porta(d: SimPorta):
        (disp.mega.abrir_porta if d.aberta else disp.mega.fechar_porta)()
        disp.tick()
        return disp.estado_publico()

    @app.post("/api/kiosk/sim/temperatura", dependencies=[Depends(so_local), Depends(so_simulado)])
    def sim_temp(d: SimTemp):
        disp.mega.definir_temperaturas(d.baia, d.cooler1, d.cooler2)
        return {"ok": True}

    @app.post("/api/kiosk/consultar", dependencies=[Depends(so_local)])
    def k_consultar(d: Consulta):
        return executar(disp.consultar, d.identificador)

    @app.post("/api/kiosk/contingencia", dependencies=[Depends(so_local)])
    def k_contingencia(d: Contingencia):
        return executar(disp.iniciar_contingencia, [i.model_dump() for i in d.itens], d.identificador)

    @app.post("/api/kiosk/reposicao", dependencies=[Depends(so_local)])
    def k_reposicao():
        return executar(disp.iniciar_reposicao)

    @app.post("/api/kiosk/liberar", dependencies=[Depends(so_local)])
    def k_liberar():
        return executar(disp.liberar)

    @app.post("/api/kiosk/confirmar", dependencies=[Depends(so_local)])
    def k_confirmar(d: Confirmacao):
        return executar(disp.confirmar, d.quantidades)

    @app.post("/api/kiosk/cancelar", dependencies=[Depends(so_local)])
    def k_cancelar():
        return executar(disp.cancelar)

    # ------------------------------------------------------------ painel: login
    @app.post("/api/auth/token")
    def token(d: Login):
        u, msg = disp.auth.por_senha(d.matricula, d.senha)
        if not u:
            raise HTTPException(401, msg)
        if u["perfil"] not in ("farmacia", "logistica", "admin"):
            raise HTTPException(403, "perfil sem acesso ao painel")
        tok = secrets.token_urlsafe(32)
        tokens[tok] = {"uid": u["id"], "perfil": u["perfil"], "nome": u["nome"], "expira": time.time() + 8 * 3600}
        disp.db.auditar("PAINEL_LOGIN", {}, usuario_id=u["id"])
        return {"token": tok, "perfil": u["perfil"], "nome": u["nome"]}

    TODOS = ("farmacia", "logistica", "admin")

    # ------------------------------------------------------------ RF06 retiradas
    @app.get("/api/movimentos")
    def movimentos(desde: float = 0, ate: float = 9e12, usuario_id: Optional[int] = None, item: Optional[str] = None,
                   tipo: Optional[str] = None, s=Depends(perfil(*TODOS))):
        return disp.db.movimentos(desde, ate, usuario_id, item, tipo)

    # ------------------------------------------------------------ RF08 estoque / RF13 notificações
    @app.get("/api/estoque")
    def estoque(s=Depends(perfil(*TODOS))):
        return {"estoque": disp.db.estoque(), "abaixo_minimo": disp.db.itens_abaixo_minimo()}

    @app.get("/api/notificacoes")
    def notificacoes(todas: bool = False, s=Depends(perfil(*TODOS))):
        return disp.db.notificacoes(not todas)

    @app.post("/api/notificacoes/{nid}/lida")
    def lida(nid: int, s=Depends(perfil(*TODOS))):
        disp.db.marcar_lida(nid)
        return {"ok": True}

    # ------------------------------------------------------------ RF10 / RF12 configuração (farmácia)
    @app.get("/api/itens")
    def itens(s=Depends(perfil(*TODOS))):
        return disp.db.itens()

    @app.put("/api/itens")
    def salvar_item(d: ItemIn, s=Depends(perfil("farmacia", "admin"))):
        executar(disp.db.salvar_item, d.codigo, d.nome, d.unidade, d.requer_refrigeracao, d.estoque_minimo)
        disp.db.auditar("CONFIG_ITEM", d.model_dump(), usuario_id=s["uid"])
        return {"ok": True}

    @app.get("/api/compartimentos")
    def compartimentos(s=Depends(perfil(*TODOS))):
        return disp.db.compartimentos()

    @app.put("/api/compartimentos")
    def salvar_comp(d: CompartimentoIn, s=Depends(perfil("farmacia", "admin"))):
        executar(disp.db.salvar_compartimento, d.id, d.nome, d.climatizado, d.ordem)
        disp.db.auditar("CONFIG_COMPARTIMENTO", d.model_dump(), usuario_id=s["uid"])
        return {"ok": True}

    @app.post("/api/alocacoes")
    def alocar(d: Alocacao, s=Depends(perfil("farmacia", "admin"))):
        executar(disp.db.alocar, d.compartimento, d.item)
        disp.db.auditar("CONFIG_ALOCACAO", d.model_dump(), usuario_id=s["uid"])
        return {"ok": True}

    @app.delete("/api/alocacoes")
    def desalocar(d: Alocacao, s=Depends(perfil("farmacia", "admin"))):
        executar(disp.db.desalocar, d.compartimento, d.item)
        disp.db.auditar("CONFIG_DESALOCACAO", d.model_dump(), usuario_id=s["uid"])
        return {"ok": True}

    @app.post("/api/ajustes")
    def ajuste(d: Ajuste, s=Depends(perfil("farmacia", "admin"))):
        saldo = executar(disp.db.movimentar, "ajuste", d.item, d.compartimento, d.quantidade, s["uid"])
        disp.db.auditar("AJUSTE_ESTOQUE", d.model_dump(), usuario_id=s["uid"])
        return {"saldo": saldo}

    @app.post("/api/contingencia")
    def contingencia(d: Ativo, s=Depends(perfil("farmacia", "admin"))):
        disp.modo_contingencia = d.ativo
        disp.db.auditar("CONTINGENCIA_" + ("HABILITADA" if d.ativo else "DESABILITADA"), {}, usuario_id=s["uid"])
        return {"contingencia": d.ativo}

    # ------------------------------------------------------------ auditoria / temperatura / mídia
    @app.get("/api/auditoria")
    def auditoria(desde: float = 0, ate: float = 9e12, tipo: Optional[str] = None, usuario_id: Optional[int] = None,
                  s=Depends(perfil("farmacia", "admin"))):
        return disp.db.auditoria(desde, ate, tipo, usuario_id)

    @app.get("/api/auditoria/verificar")
    def verificar(s=Depends(perfil("farmacia", "admin"))):
        return disp.db.verificar_cadeia()

    @app.get("/api/temperaturas")
    def temperaturas(horas: float = 24, s=Depends(perfil(*TODOS))):
        return {"atual": disp.temp, "faixa": [disp.cfg.temp_min_c, disp.cfg.temp_max_c],
                "historico": disp.db.temperaturas(time.time() - horas * 3600)}

    @app.get("/api/mega/eventos")
    def mega_eventos(s=Depends(perfil("farmacia", "admin"))):
        return {"online": disp.mega.online, "estado": disp.mega.estado(), "eventos": disp.db.mega_eventos()}

    @app.get("/api/midia/{caminho:path}")
    def midia(caminho: str, s=Depends(perfil("farmacia", "admin"))):
        base = os.path.realpath(os.path.join(disp.cfg.dados_dir, "midia"))
        alvo = os.path.realpath(os.path.join(disp.cfg.dados_dir, caminho))
        if not alvo.startswith(base + os.sep) or not os.path.isfile(alvo):
            raise HTTPException(404, "mídia não encontrada")
        disp.db.auditar("MIDIA_ACESSADA", {"arquivo": caminho}, usuario_id=s["uid"])
        return FileResponse(alvo)

    # ------------------------------------------------------------ usuários (TI/admin)
    @app.get("/api/usuarios")
    def usuarios(s=Depends(perfil("admin", "farmacia"))):
        return disp.db.usuarios()

    @app.post("/api/usuarios")
    def criar_usuario(d: UsuarioIn, s=Depends(perfil("admin"))):
        h = None
        if d.senha:
            executar(A.validar_politica, d.senha)
            h = A.gerar_hash(d.senha)
        uid = executar(disp.db.criar_usuario, d.matricula, d.nome, d.perfil, h)
        disp.db.auditar("USUARIO_CRIADO", {"id": uid, "matricula": d.matricula, "perfil": d.perfil}, usuario_id=s["uid"])
        return {"id": uid}

    @app.post("/api/usuarios/{uid}/senha_porta")
    def senha_porta(uid: int, d: SenhaPorta, s=Depends(perfil("admin"))):
        return {"mega_id": executar(disp.criar_usuario_porta, uid, d.senha, s["uid"])}

    @app.post("/api/usuarios/{uid}/digital")
    def digital(uid: int, s=Depends(perfil("admin"))):
        return {"mega_id": executar(disp.cadastrar_digital, uid, s["uid"])}

    @app.post("/api/usuarios/{uid}/ativo")
    def ativo(uid: int, d: Ativo, s=Depends(perfil("admin"))):
        return executar(disp.definir_ativo, uid, d.ativo, s["uid"])

    return app
