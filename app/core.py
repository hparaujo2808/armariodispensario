"""Núcleo do app do notebook: a sessão de retirada/reposição, guiada pelos eventos do Mega.

O Mega cuida da porta (digital, senha, trava, sensor da porta, frio). O notebook
cuida do resto: CPF, MV, gravação das câmeras, registro de auditoria e estoque.

  OCIOSO --Mega AUTH_OK--> AUTENTICADO --CPF (MV)--> PRESCRICAO --liberar() (LIB ao Mega)--> LIBERADO
     ^                         | (logística/farmácia: reposição) ---------------------------------^  |
     |                                                                         Mega PORTA_ABERTA  |
     +--confirmar()-- CONFIRMACAO <--Mega PORTA_FECHADA (para as câmeras)-- PORTA_ABERTA <--------+

A dupla confirmação da retirada (pedido do hospital): os itens são conferidos na
tela antes de liberar a porta e as quantidades são confirmadas depois de fechar.
Cada evento do Mega é gravado (somente-inserção) antes de ser confirmado a ele.
O estado da sessão fica no banco (journal) e volta depois de uma queda (RNF07.1).
"""
from __future__ import annotations

import datetime as dt
import logging
import os
import threading
import time
import uuid
from typing import Callable, Dict, List, Optional

from .auth import Autenticador
from .cameras import Cameras
from .config import Config
from .hal.base import Mega
from .mv_client import ErroMV
from .protocolo import METODOS
from .storage import Banco

log = logging.getLogger(__name__)

OCIOSO, AUTENTICADO, PRESCRICAO, LIBERADO, PORTA_ABERTA, CONFIRMACAO = (
    "OCIOSO", "AUTENTICADO", "PRESCRICAO", "LIBERADO", "PORTA_ABERTA", "CONFIRMACAO")

# eventos do Mega que viram alarme na tela (e quando acabam)
ALARMES_MEGA = {
    "PORTA_ABERTA_TEMPO": "PORTA_ABERTA_TEMPO", "ABERTURA_NAO_AUTORIZADA": "ABERTURA_NAO_AUTORIZADA",
    "TEMP_ALARME": "TEMPERATURA_FORA_FAIXA", "SENSOR_FALHA": "FALHA_SENSOR", "CORTE_QUENTE": "SOBRETEMPERATURA_DISSIPADOR",
    "FRIO_SEM_EFEITO": "BAIA_NAO_ESFRIA",
    "ENERGIA_FALTA": "FALHA_ENERGIA", "BLOQUEIO": "BLOQUEIO_POR_ERROS",
}
FIM_ALARME = {"TEMP_NORMAL": "TEMPERATURA_FORA_FAIXA", "ENERGIA_VOLTA": "FALHA_ENERGIA"}
LACUNA_MAX_S = 60.0
JANELA_ABERTURA_S = 5.0  # firmware: par::JANELA_ABERTURA_MS     # quanto esperar um evento do Mega que faltou antes de dar como perdido


class ErroOperacao(Exception):
    pass


class Dispensario:
    def __init__(self, cfg: Config, mega: Mega, banco: Banco, mv, cameras: Optional[Cameras] = None,
                 relogio: Callable[[], float] = time.time):
        self.cfg = cfg
        self.mega = mega
        self.db = banco
        self.mv = mv
        self.agora = relogio
        self.cameras = cameras or Cameras(cfg.cameras, os.path.join(cfg.dados_dir, "midia"), cfg.video_fps, cfg.video_max_s)
        self.auth = Autenticador(banco, cfg.max_tentativas_senha, cfg.bloqueio_s, relogio)
        self._lock = threading.RLock()
        self.sessao: Optional[dict] = None
        self.mensagem = "Use a digital ou o ID + senha no teclado da porta"
        self.alarmes: Dict[str, float] = {}
        self.temp: Dict[str, object] = {}
        self._ult_temp = 0.0
        self._ult_volume = None
        self._gravacao_sem_sessao: Optional[str] = None
        self._lacuna_desde: Optional[float] = None
        self.modo_contingencia = False
        self._recuperar_sessao()
        self.db.auditar("SISTEMA_INICIADO", {"dispensario": cfg.dispensario_id, "setor": cfg.setor})

    # ================================================================ utilitários
    @property
    def estado(self) -> str:
        return self.sessao["estado"] if self.sessao else OCIOSO

    def _persistir(self) -> None:
        self.db.salvar_sessao(self.sessao)

    def _ir(self, estado: str, **campos) -> None:
        self.sessao.update(campos)
        self.sessao["estado"] = estado
        self.sessao["ultima_atividade"] = self.agora()
        self._persistir()

    def _aud(self, tipo: str, dados: Optional[dict] = None, midia: Optional[list] = None) -> None:
        s = self.sessao
        self.db.auditar(tipo, dados or {}, usuario_id=s["usuario"]["id"] if s else None,
                        sessao_id=s["id"] if s else None, midia=midia)

    def _encerrar(self, motivo: str, msg: str, cancelar_mega: bool = False) -> None:
        if self.sessao:
            self._aud("SESSAO_ENCERRADA", {"motivo": motivo})
            if cancelar_mega and self.sessao["estado"] in (AUTENTICADO, PRESCRICAO):
                self.mega.cancelar()
        self.sessao = None
        self._persistir()
        self.mensagem = msg

    def _requer(self, *estados: str) -> None:
        if self.estado not in estados:
            raise ErroOperacao(f"operação inválida no estado {self.estado}")

    def _noite(self) -> bool:
        h = dt.datetime.fromtimestamp(self.agora()).hour
        a, b = self.cfg.noite_inicio_h, self.cfg.noite_fim_h
        return h >= a or h < b if a > b else a <= h < b

    def _prefixo_midia(self, rotulo: str) -> str:
        sid = self.sessao["id"] if self.sessao else "sem_sessao"
        dia = dt.datetime.fromtimestamp(self.agora()).strftime("%Y-%m-%d")
        return os.path.join(self.cfg.dados_dir, "midia", dia, f"{sid}_{rotulo}_{int(self.agora() * 1000)}")

    def _parar_cameras(self) -> list:
        midia, erros = self.cameras.parar(self.cfg.dados_dir)
        if erros or not midia:
            self.alarmes.setdefault("FALHA_CAMERA", self.agora())
            self.db.auditar("FALHA_CAMERA", {"erros": erros}, sessao_id=self.sessao["id"] if self.sessao else None)
        else:
            self.alarmes.pop("FALHA_CAMERA", None)
        return midia

    # ============================================================ recuperação
    def _recuperar_sessao(self) -> None:
        s = self.db.sessao_pendente()
        if not s:
            return
        est = s["estado"]
        if est in (AUTENTICADO, PRESCRICAO, LIBERADO):
            # o Mega reinicia junto ou expira a liberação: a pessoa autentica de novo
            self.db.auditar("SESSAO_DESCARTADA_REINICIO", {"estado": est}, usuario_id=s["usuario"]["id"], sessao_id=s["id"])
            self.db.salvar_sessao(None)
            return
        self.sessao = s
        s["recuperada"] = True
        s["estado"] = CONFIRMACAO            # porta aberta ou fechada: termina pela confirmação
        s["ultima_atividade"] = self.agora()
        self._persistir()
        self.db.auditar("SESSAO_RECUPERADA", {"estado_anterior": est}, usuario_id=s["usuario"]["id"], sessao_id=s["id"])
        self.mensagem = "Operação interrompida foi recuperada. Confira e confirme as quantidades."

    # ============================================================ eventos do Mega
    def _hora_do_evento(self, ev: dict) -> Optional[float]:
        """Hora em que o evento aconteceu no Mega, pelo par (boot, ms) da última linha ST.

        Só muda algo para eventos guardados (notebook fora do ar): o resto chega na hora.
        """
        rel = self.mega.relogio()
        if not rel or rel[1] != ev["b"]:
            return None
        atraso = ((rel[2] - ev["ms"]) % 2**32) / 1000.0
        return rel[0] - atraso if atraso > 2.0 else None

    def _evento_mega(self, ev: dict) -> None:
        res = self.db.registrar_mega_evento(ev)
        if res == "repetido":                            # o Mega reenvia até o ACK
            return
        if res == "nova_epoca":
            self.db.auditar("MEGA_SEQUENCIA_REINICIADA", {"seq": ev["seq"], "boot": ev["b"]})
            self.db.notificar("MEGA_SEQUENCIA_REINICIADA",
                              "A memória do controlador foi zerada ou a placa foi trocada: conferir as senhas da porta.")
        t = ev["t"]
        dados = {"seq": ev["seq"], "boot": ev["b"], "ms_mega": ev["ms"], "usuario_mega": ev["u"], "valor": ev["v"]}
        quando = self._hora_do_evento(ev)
        if quando is not None:
            dados["hora_estimada"] = True                # RF05: hora do Mega, não a da chegada
        u = self.db.usuario(mega_id=ev["u"]) if ev["u"] else None
        self.db.auditar("MEGA_" + t, dados, usuario_id=u["id"] if u else None,
                        sessao_id=self.sessao["id"] if self.sessao else None, ts=quando)

        if t in ALARMES_MEGA:
            nome = ALARMES_MEGA[t]
            self.alarmes.setdefault(nome, self.agora())
            if nome in ("TEMPERATURA_FORA_FAIXA", "FALHA_SENSOR", "SOBRETEMPERATURA_DISSIPADOR", "BAIA_NAO_ESFRIA"):
                self.db.notificar(nome, f"Baia fria: {nome.replace('_', ' ').lower()} (valor {ev['v'] / 10:.1f})")
        if t in FIM_ALARME:
            self.alarmes.pop(FIM_ALARME[t], None)

        if t == "AUTH_OK":
            self._autenticado(ev["u"], METODOS.get(ev["v"], "?"))
        elif t == "AUTH_FALHA":
            self.mensagem = "Digital ou senha não reconhecida. Tente de novo na porta."
        elif t == "BLOQUEIO":
            self.mensagem = f"Teclado bloqueado por {ev['v']} s depois de 3 erros"
        elif t == "LIBERACAO_EXPIROU" and self.estado == LIBERADO:
            # o Mega ainda aceita a abertura por JANELA_ABERTURA_S (o reed abre depois da lingueta)
            self.sessao["expirou_em"] = self.agora()
        elif t == "CANCELADO" and self.estado in (AUTENTICADO, PRESCRICAO):
            self._encerrar("cancelada_no_mega", "Operação cancelada na porta")
        elif t == "PORTA_ABERTA":
            self._abriu(ev)
        elif t == "ABERTURA_NAO_AUTORIZADA":
            self._gravacao_sem_sessao = self._prefixo_midia("nao_autorizada")
            self.cameras.iniciar(self._gravacao_sem_sessao)
        elif t == "PORTA_FECHADA":
            self._fechou(ev)
            self.alarmes.pop("PORTA_ABERTA_TEMPO", None)
            self.alarmes.pop("ABERTURA_NAO_AUTORIZADA", None)
        elif t == "DIGITAL_CADASTRADA" and u:
            self.db.atualizar_usuario(u["id"], digital_slot=ev["v"])
        elif t == "MODO_AUTONOMO":
            self.db.notificar("MODO_AUTONOMO", "O Mega liberou a porta sem o notebook: conferir a retirada pelas imagens.")
        elif t in ("BOOT", "RECUPERADO") and self.estado == LIBERADO:
            self._encerrar("mega_reiniciou", "O controlador reiniciou. Autentique de novo.")

    def _confirmar_mega(self) -> None:
        """ACK do Mega é cumulativo: só confirma até o último evento sem buraco antes dele.

        Se faltar um evento por mais de LACUNA_MAX_S (o Mega já o tirou da fila), a falta
        fica registrada na auditoria e a confirmação segue (revisão independente, item 7).
        """
        contig, maior = self.db.mega_contiguo()
        if maior > contig:
            if self._lacuna_desde is None:
                self._lacuna_desde = self.agora()
            elif self.agora() - self._lacuna_desde > LACUNA_MAX_S:
                faltam = self.db.mega_faltando(contig + 1, maior)
                for seq in faltam:
                    self.db.registrar_mega_evento({"seq": seq, "b": 0, "ms": 0, "t": "PERDIDO", "u": 0, "v": 0})
                self.db.auditar("MEGA_EVENTOS_PERDIDOS", {"seqs": faltam[:50], "total": len(faltam)})
                self.db.notificar("MEGA_EVENTOS_PERDIDOS", f"{len(faltam)} evento(s) do controlador não chegaram")
                self._lacuna_desde = None
                contig = maior
        else:
            self._lacuna_desde = None
        if contig:
            self.mega.confirmar(contig)

    def _autenticado(self, mega_id: int, metodo: str) -> None:
        u = self.db.usuario(mega_id=mega_id)
        if not u or not u["ativo"]:
            self.db.auditar("USUARIO_MEGA_DESCONHECIDO", {"mega_id": mega_id})
            self.mega.cancelar()
            self.mensagem = "Usuário sem cadastro neste dispensário"
            return
        if self.estado != OCIOSO:
            self.db.auditar("AUTH_IGNORADA_SESSAO_ATIVA", {"mega_id": mega_id}, usuario_id=u["id"])
            return
        self.sessao = {
            "id": uuid.uuid4().hex[:12], "estado": AUTENTICADO, "metodo": metodo,
            "usuario": {"id": u["id"], "nome": u["nome"], "perfil": u["perfil"], "matricula": u["matricula"],
                        "mega_id": mega_id},
            "inicio": self.agora(), "ultima_atividade": self.agora(), "modo": None, "itens": [],
        }
        self._persistir()
        self.alarmes.pop("BLOQUEIO_POR_ERROS", None)
        self.mensagem = f"Olá, {u['nome'].split()[0]}. Digite o CPF ou o código da receita."

    def _abriu(self, ev: dict) -> None:
        if self.estado == LIBERADO and ev["u"] == self.sessao["usuario"]["mega_id"]:
            self._ir(PORTA_ABERTA, aberta_em=self.agora(), prefixo_midia=self._prefixo_midia("abertura"))
            self.cameras.iniciar(self.sessao["prefixo_midia"])
            s = self.sessao
            # RF05: usuário + horário exato de cada abertura (o vídeo entra no fechamento, com o hash)
            self._aud("ABERTURA", {"modo": s["modo"], "paciente_ref": s.get("paciente_ref"),
                                   "prescricao_id": s.get("prescricao_id"), "metodo": s["metodo"],
                                   "itens": [(i["codigo"], i["qtd_retirar"]) for i in s["itens"]]})
            self.mensagem = "Retire os itens indicados e feche a porta"
        else:
            # o Mega liberou sem o notebook (modo autônomo): grava assim mesmo
            self._gravacao_sem_sessao = self._prefixo_midia("abertura_sem_sessao")
            self.cameras.iniciar(self._gravacao_sem_sessao)
            self.db.auditar("ABERTURA_SEM_SESSAO", {"usuario_mega": ev["u"]})

    def _fechou(self, ev: dict) -> None:
        midia = self._parar_cameras()
        if self.estado == PORTA_ABERTA:
            dur = round(self.agora() - self.sessao.get("aberta_em", self.agora()), 1)
            self._ir(CONFIRMACAO, fechada_em=self.agora(), midia=midia)
            self._aud("FECHAMENTO", {"duracao_s": dur}, midia)   # RF07: mídia ligada ao evento, com SHA-256
            self.mensagem = ("Informe as quantidades repostas" if self.sessao["modo"] == "reposicao"
                             else "Confirme as quantidades retiradas")
        else:
            self.db.auditar("FECHAMENTO_SEM_SESSAO", {"duracao_s": ev["v"]}, midia=midia)
            self._gravacao_sem_sessao = None

    # ============================================================ retirada
    def cancelar(self) -> dict:
        with self._lock:
            self._requer(AUTENTICADO, PRESCRICAO)
            self._encerrar("cancelada", "Operação cancelada", cancelar_mega=True)
            return self.estado_publico()

    def consultar(self, identificador: str) -> dict:
        """RF03/RF04: busca a prescrição no MV pelo CPF ou código de receita."""
        with self._lock:
            self._requer(AUTENTICADO, PRESCRICAO)
            if self.sessao["usuario"]["perfil"] not in ("enfermagem", "farmacia", "admin"):
                raise ErroOperacao("perfil sem permissão de retirada")
            ident = identificador.strip()
            if len("".join(c for c in ident if c.isalnum())) < 4:
                raise ErroOperacao("Identificador inválido")
            try:
                p = self.mv.consultar_prescricao(ident)
            except ErroMV as e:
                self._aud("MV_INDISPONIVEL", {"erro": str(e)})
                raise ErroOperacao("Sistema MV indisponível. Acione a farmácia (modo contingência).")
            ref, mask = self.db.pseudonimo(ident), self.db.mascarar(ident)
            if p is None:
                self._aud("PRESCRICAO_NAO_ENCONTRADA", {"paciente_ref": ref})
                raise ErroOperacao("Nenhuma prescrição ativa para este paciente")
            itens = [self._linha_item(i.codigo, i.descricao, i.quantidade, i.posologia) for i in p.itens]
            self._ir(PRESCRICAO, modo="retirada", itens=itens, paciente_ref=ref, paciente_mask=mask,
                     paciente_nome=p.paciente_nome, leito=p.leito, prescricao_id=p.prescricao_id)
            self._aud("PRESCRICAO_CONSULTADA", {"paciente_ref": ref, "prescricao_id": p.prescricao_id,
                                                "itens": [(i["codigo"], i["qtd_prescrita"]) for i in itens]})
            self.mensagem = "Confira os itens e toque em 'Liberar porta'"
            return self.estado_publico()

    def _linha_item(self, codigo: str, descricao: str, qtd: int, posologia: str = "") -> dict:
        cad = self.db.item(codigo)
        locais = self.db.localizar(codigo) if cad else []
        saldo = sum(l["quantidade"] for l in locais)
        return {"codigo": codigo, "descricao": descricao, "posologia": posologia,
                "qtd_prescrita": qtd, "qtd_retirar": min(qtd, saldo), "saldo": saldo, "disponivel": saldo > 0,
                "refrigerado": bool(cad and cad["requer_refrigeracao"]),
                "locais": [{"compartimento": l["compartimento"], "nome": l["nome"], "quantidade": l["quantidade"]}
                           for l in locais if l["quantidade"] > 0]}

    def iniciar_contingencia(self, itens: List[dict], identificador: str) -> dict:
        """Risco 2: MV fora do ar. Só farmácia/admin, ou com a contingência habilitada; marcado na auditoria."""
        with self._lock:
            self._requer(AUTENTICADO)
            if self.sessao["usuario"]["perfil"] not in ("farmacia", "admin") and not self.modo_contingencia:
                raise ErroOperacao("Contingência não habilitada pela farmácia")
            lista = []
            for it in itens:
                cad = self.db.item(it["codigo"])
                if not cad:
                    raise ErroOperacao(f"item {it['codigo']} não cadastrado")
                lista.append(self._linha_item(cad["codigo"], cad["nome"], int(it["quantidade"])))
            self._ir(PRESCRICAO, modo="contingencia", itens=lista, paciente_ref=self.db.pseudonimo(identificador),
                     paciente_mask=self.db.mascarar(identificador), paciente_nome="(contingência)", leito="",
                     prescricao_id=None)
            self._aud("CONTINGENCIA_INICIADA", {"itens": [(i["codigo"], i["qtd_prescrita"]) for i in lista]})
            return self.estado_publico()

    def iniciar_reposicao(self) -> dict:
        """RF11: logística/farmácia abastece o dispensário."""
        with self._lock:
            self._requer(AUTENTICADO)
            if self.sessao["usuario"]["perfil"] not in ("logistica", "farmacia", "admin"):
                raise ErroOperacao("perfil sem permissão de reposição")
            self._ir(PRESCRICAO, modo="reposicao", itens=[])
            self._aud("REPOSICAO_INICIADA")
            return self.liberar()

    def liberar(self) -> dict:
        with self._lock:
            self._requer(PRESCRICAO)
            if self.sessao["modo"] != "reposicao" and not any(i["disponivel"] and i["qtd_retirar"] > 0 for i in self.sessao["itens"]):
                raise ErroOperacao("Nenhum item prescrito disponível neste dispensário")
            self._ir(LIBERADO, liberado_em=self.agora())      # journal antes do efeito físico (RNF07.1)
            if not self.mega.liberar(self.sessao["usuario"]["mega_id"]):
                self._encerrar("mega_recusou", "O controlador da porta não liberou. Autentique de novo na porta.")
                raise ErroOperacao("O controlador da porta não liberou (a autenticação na porta expirou?)")
            self._aud("PORTA_LIBERADA", {"modo": self.sessao["modo"]})
            self.mensagem = "Porta liberada: abra agora"
            return self.estado_publico()

    def confirmar(self, quantidades: Optional[Dict[str, int]] = None, automatico: bool = False) -> dict:
        """Retirada: {codigo: qtd}. Reposição: {"COMPARTIMENTO|codigo": qtd}."""
        with self._lock:
            self._requer(CONFIRMACAO)
            s = self.sessao
            uid = s["usuario"]["id"]
            with self.db.transacao():          # tudo ou nada: sem baixa pela metade
                if s["modo"] == "reposicao":
                    registros = []
                    for chave, q in (quantidades or {}).items():
                        q = int(q)
                        if q <= 0:
                            continue
                        comp, item = chave.split("|", 1)
                        saldo = self.db.movimentar("reposicao", item, comp, q, uid, sessao_id=s["id"])
                        registros.append({"compartimento": comp, "item": item, "quantidade": q, "saldo": saldo})
                    self._aud("REPOSICAO_REGISTRADA", {"registros": registros}, s.get("midia"))
                    for r in self.db.notificacoes():
                        if r["tipo"] == "ESTOQUE_BAIXO" and r["item"] in {x["item"] for x in registros}:
                            self.db.marcar_lida(r["id"])
                else:
                    retirados, divergencias = [], []
                    for it in s["itens"]:
                        q = it["qtd_retirar"] if quantidades is None else int(quantidades.get(it["codigo"], 0))
                        if q < 0 or q > it["saldo"]:
                            raise ErroOperacao(f"quantidade inválida para {it['descricao']}")
                        if q != it["qtd_prescrita"]:
                            divergencias.append({"codigo": it["codigo"], "prescrito": it["qtd_prescrita"], "retirado": q})
                        restante = q
                        for loc in it["locais"]:                 # baixa nos compartimentos, do maior saldo
                            if restante <= 0:
                                break
                            tira = min(restante, loc["quantidade"])
                            if tira > 0:
                                self.db.movimentar("retirada", it["codigo"], loc["compartimento"], tira, uid,
                                                   s.get("paciente_ref"), s.get("prescricao_id"), s["id"])
                                restante -= tira
                        if q:
                            retirados.append({"codigo": it["codigo"], "quantidade": q})
                    self._aud("RETIRADA_REGISTRADA", {"modo": s["modo"], "automatica": automatico,
                                                      "paciente_ref": s.get("paciente_ref"),
                                                      "prescricao_id": s.get("prescricao_id"), "itens": retirados},
                              s.get("midia"))
                    if divergencias:
                        self._aud("DIVERGENCIA_PRESCRICAO", {"divergencias": divergencias})
                    if automatico:
                        self.db.notificar("CONFIRMACAO_AUTOMATICA",
                                          f"Retirada de {s['usuario']['nome']} confirmada automaticamente — conferir o vídeo.")
                    if s.get("prescricao_id"):
                        self.db.enfileirar_mv({"sessao_id": s["id"], "dispensario": self.cfg.dispensario_id,
                                               "prescricao_id": s["prescricao_id"], "usuario_matricula": s["usuario"]["matricula"],
                                               "ts": self.agora(), "itens": retirados, "divergencias": divergencias})
                    self._verificar_estoque_baixo([r["codigo"] for r in retirados])
            self._encerrar("concluida", "Operação registrada. Obrigado!")
            return self.estado_publico()

    def _verificar_estoque_baixo(self, codigos: List[str]) -> None:
        """RF13: notificação de estoque mínimo para a logística."""
        for r in self.db.itens_abaixo_minimo():
            if r["codigo"] in codigos and self.db.notificar(
                    "ESTOQUE_BAIXO", f"{r['nome']}: saldo {r['saldo']} (mínimo {r['estoque_minimo']})", r["codigo"]):
                self.db.auditar("ESTOQUE_BAIXO", {"item": r["codigo"], "saldo": r["saldo"]})

    # ============================================================ laço
    def tick(self) -> None:
        """Processa os eventos do Mega e as temporizações. Chamado ~10x/s."""
        with self._lock:
            agora = self.agora()
            self.mega.tick(agora)
            evs = self.mega.eventos()
            for ev in evs:
                try:
                    self._evento_mega(ev)
                except Exception:   # noqa: BLE001 — um evento ruim não pode parar o laço
                    log.exception("erro ao tratar evento do Mega %s", ev)
            if evs or self._lacuna_desde is not None:
                self._confirmar_mega()
            self.temp = self.mega.temperaturas()
            if agora - self._ult_temp >= 60 and self.temp.get("baia") is not None:
                self._ult_temp = agora
                q = [t for t in (self.temp.get("cooler1"), self.temp.get("cooler2")) if t is not None]
                self.db.registrar_temperatura(self.temp.get("baia"), max(q) if q else None, None,
                                              (int(bool(self.temp.get("peltier1"))) + int(bool(self.temp.get("peltier2")))) / 2)
            vol = self.cfg.volume_noite if self._noite() else self.cfg.volume_dia   # RNF10: mais baixo à noite
            if vol != self._ult_volume and self.mega.online and self.mega.ajustar(vol=vol):
                self._ult_volume = vol
            s = self.sessao
            if s and self.estado == LIBERADO and s.get("expirou_em") and agora - s["expirou_em"] > JANELA_ABERTURA_S:
                self._encerrar("liberacao_expirou", "A porta não foi aberta a tempo. Autentique de novo.")
            elif s and self.estado in (AUTENTICADO, PRESCRICAO) and agora - s["ultima_atividade"] > self.cfg.sessao_inatividade_s:
                self._encerrar("inatividade", "Sessão encerrada por inatividade", cancelar_mega=True)
            elif s and self.estado == CONFIRMACAO and agora - s["ultima_atividade"] > self.cfg.confirmacao_automatica_s:
                try:
                    self.confirmar(None, automatico=True)
                except Exception as e:   # noqa: BLE001 — ex.: saldo mudou no painel no meio da retirada
                    self.db.auditar("CONFIRMACAO_AUTOMATICA_FALHOU", {"erro": str(e)}, usuario_id=s["usuario"]["id"],
                                    sessao_id=s["id"], midia=s.get("midia"))
                    self.db.notificar("CONFIRMACAO_AUTOMATICA_FALHOU",
                                      f"Retirada de {s['usuario']['nome']} não foi baixada ({e}) — conferir o vídeo.")
                    self._encerrar("confirmacao_falhou", "Retirada não registrada: avise a farmácia")

    # ============================================================ outbox MV e mídia
    def enviar_pendentes_mv(self) -> int:
        enviados = 0
        for p in self.db.pendentes_mv():
            ok = self.mv.informar_dispensacao(p["payload"])
            self.db.marcar_mv(p["id"], ok)
            if not ok:
                break
            enviados += 1
        return enviados

    def expurgar_midia(self) -> int:
        limite = self.agora() - self.cfg.midia_retencao_dias * 86400
        base = os.path.join(self.cfg.dados_dir, "midia")
        n = 0
        for raiz, _, arquivos in os.walk(base):
            for a in arquivos:
                p = os.path.join(raiz, a)
                if os.path.getmtime(p) < limite:
                    os.remove(p)
                    n += 1
        if n:
            self.db.auditar("MIDIA_EXPURGADA", {"arquivos": n, "retencao_dias": self.cfg.midia_retencao_dias})
        return n

    # ============================================================ administração
    def criar_usuario_porta(self, uid: int, senha_porta: str, operador_id: int) -> int:
        """Dá ao usuário um número no Mega e define a senha da porta (guardada só como hash, no Mega)."""
        u = self.db.usuario(uid=uid)
        if not u:
            raise ErroOperacao("usuário inexistente")
        mega_id = u["mega_id"] or self.db.proximo_mega_id()
        if not self.mega.definir_senha(mega_id, senha_porta):
            raise ErroOperacao("O Mega recusou a senha (4 a 8 dígitos) ou não respondeu")
        self.db.atualizar_usuario(uid, mega_id=mega_id)
        self.db.auditar("SENHA_PORTA_DEFINIDA", {"usuario": uid, "mega_id": mega_id}, usuario_id=operador_id)
        return mega_id

    def definir_ativo(self, uid: int, ativo: bool, operador_id: int) -> dict:
        """Desativar também apaga o usuário no Mega; senão ele abriria a porta no modo autônomo."""
        u = self.db.usuario(uid=uid)
        if not u:
            raise ErroOperacao("usuário inexistente")
        self.db.atualizar_usuario(uid, ativo=int(ativo))
        self.db.auditar("USUARIO_" + ("ATIVADO" if ativo else "DESATIVADO"), {"id": uid}, usuario_id=operador_id)
        if ativo:
            aviso = "Defina de novo a senha da porta e a digital deste usuário" if u["mega_id"] else ""
            return {"ok": True, "aviso": aviso}
        if u["mega_id"] and not self.mega.desativar(u["mega_id"]):
            self.db.auditar("DESATIVACAO_MEGA_PENDENTE", {"id": uid, "mega_id": u["mega_id"]}, usuario_id=operador_id)
            raise ErroOperacao("Desativado no sistema, mas o controlador da porta não respondeu: repita com ele ligado")
        return {"ok": True, "aviso": ""}

    def cadastrar_digital(self, uid: int, operador_id: int) -> int:
        u = self.db.usuario(uid=uid)
        if not u or not u["mega_id"]:
            raise ErroOperacao("defina primeiro a senha da porta deste usuário")
        if not self.mega.cadastrar_digital(u["mega_id"]):
            raise ErroOperacao("O Mega não começou o cadastro (porta em uso ou leitor ausente)")
        self.db.auditar("CADASTRO_DIGITAL_INICIADO", {"usuario": uid, "mega_id": u["mega_id"]}, usuario_id=operador_id)
        return u["mega_id"]

    # ============================================================ visão para a tela
    def estado_publico(self) -> dict:
        s = self.sessao
        st = self.mega.estado()
        return {
            "estado": self.estado,
            "mensagem": self.mensagem,
            "usuario": s["usuario"] if s else None,
            "modo": s.get("modo") if s else None,
            "paciente": ({"mascara": s.get("paciente_mask"), "nome": s.get("paciente_nome"), "leito": s.get("leito")}
                         if s and s.get("paciente_ref") else None),
            "itens": s.get("itens", []) if s else [],
            "recuperada": bool(s and s.get("recuperada")),
            "porta_aberta": st.get("e") == "PORTA_ABERTA",
            "gravando": self.cameras.gravando,
            "alarmes": sorted(self.alarmes),
            "mega_online": self.mega.online,
            "mega_estado": st.get("e"),
            "energia_rede": "FALHA_ENERGIA" not in self.alarmes,
            "temperatura_frio": self.temp.get("baia"),
            "estoque_reposicao": self.db.estoque() if s and s.get("modo") == "reposicao" else [],
            "contingencia": self.modo_contingencia,
            "simulado": self.cfg.porta_serial == "sim",
        }
