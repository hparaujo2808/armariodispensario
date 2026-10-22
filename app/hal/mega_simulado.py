"""Mega simulado, em Python: imita o firmware (src/logica/maquina.cpp) no que
importa para o notebook. Serve para:
  - demonstrar o fluxo sem o armário (botões de simulação no quiosque);
  - testar o app (tests/test_app.py).

Como o Mega de verdade, repete os eventos até receber ACK.
"""
from __future__ import annotations

import time
from typing import Callable, Dict, List, Optional

from .base import Mega

TRAVA_MAX_S = 3.0
AGUARDA_NOTEBOOK_S = 120.0
BLOQUEIO_S = 30.0


class MegaSimulado(Mega):
    online = True

    def __init__(self, relogio: Callable[[], float] = time.time):
        self.agora = relogio
        self.e = "OCIOSO"
        self.u = 0
        self.desde = self.agora()
        self.porta_aberta = False
        self.alarme_porta_s = 30.0
        self.aviso_tempo = False
        self.erros = 0
        self.senhas: Dict[int, str] = {1: "1357"}
        self.digitais: Dict[int, int] = {}
        self._seq = 0
        self._pendentes: Dict[int, dict] = {}
        self.temp = {"baia": 5.4, "cooler1": 38.0, "cooler2": 37.5, "peltier1": False, "peltier2": False,
                     "alarme": False, "v12": 12.0}
        self.comandos: List[str] = []
        self._ev("BOOT", 0, 0)

    # ---------------------------------------------------------- utilidades
    def _ev(self, t: str, u: int, v: int) -> None:
        self._seq += 1
        self._pendentes[self._seq] = {"seq": self._seq, "t": t, "u": u, "v": v, "ms": int(self.agora() * 1000) % 2**32, "b": 1}

    def _ir(self, e: str) -> None:
        self.e = e
        self.desde = self.agora()

    # ------------------------------------------- ações de quem está na porta
    def autenticar(self, mega_id: int, metodo: str = "digital", senha: Optional[str] = None) -> bool:
        if self.e != "OCIOSO":
            return False
        ok = mega_id in self.senhas and (metodo == "digital" or senha == self.senhas[mega_id])
        if not ok:
            return self.errar(metodo)
        self.erros = 0
        self.u = mega_id
        self._ev("AUTH_OK", mega_id, 1 if metodo == "digital" else 2)
        self._ir("AGUARDANDO_NOTEBOOK")
        return True

    def errar(self, metodo: str = "senha") -> bool:
        self.erros += 1
        self._ev("AUTH_FALHA", 0, 1 if metodo == "digital" else 2)
        if self.erros >= 3:
            self._ev("BLOQUEIO", 0, int(BLOQUEIO_S))
            self._ir("BLOQUEADO")
        return False

    def abrir_porta(self) -> None:
        if self.porta_aberta:
            return
        self.porta_aberta = True
        self.aviso_tempo = False
        if self.e == "LIBERADO":
            self._ev("PORTA_ABERTA", self.u, 0)
        else:
            self._ev("ABERTURA_NAO_AUTORIZADA", 0, 0)
            self.u = 0
        self._ir("PORTA_ABERTA")

    def fechar_porta(self) -> None:
        if not self.porta_aberta:
            return
        self.porta_aberta = False
        if self.e == "PORTA_ABERTA":
            self._ev("PORTA_FECHADA", self.u, int(self.agora() - self.desde))
            self.u = 0
            self._ir("OCIOSO")

    def definir_temperaturas(self, baia: float, cooler1: float = 38.0, cooler2: float = 38.0) -> None:
        self.temp.update(baia=baia, cooler1=cooler1, cooler2=cooler2)

    # ----------------------------------------------------------- interface
    def eventos(self) -> List[dict]:
        return [dict(e) for _, e in sorted(self._pendentes.items())]

    def confirmar(self, seq: int) -> None:
        for s in [s for s in self._pendentes if s <= seq]:
            del self._pendentes[s]

    def estado(self):
        return {"e": self.e, "u": str(self.u), "pend": str(len(self._pendentes))}

    def temperaturas(self):
        return dict(self.temp)

    def liberar(self, mega_id: int) -> bool:
        self.comandos.append(f"LIB {mega_id}")
        if self.e != "AGUARDANDO_NOTEBOOK" or mega_id != self.u:
            return False
        self._ev("LIBERADO", self.u, 0)
        self._ir("LIBERADO")
        return True

    def cancelar(self) -> bool:
        self.comandos.append("CANC")
        if self.e != "AGUARDANDO_NOTEBOOK":
            return False
        self._ev("CANCELADO", self.u, 0)
        self.u = 0
        self._ir("OCIOSO")
        return True

    def cadastrar_digital(self, mega_id: int) -> bool:
        if self.e != "OCIOSO" or mega_id not in self.senhas:
            return False
        self.digitais[mega_id] = mega_id
        self._ev("DIGITAL_CADASTRADA", mega_id, mega_id)
        return True

    def definir_senha(self, mega_id: int, senha: str) -> bool:
        if not (1 <= mega_id <= 20 and senha.isdigit() and 4 <= len(senha) <= 8):
            return False
        self.senhas[mega_id] = senha
        self._ev("SENHA_ALTERADA", mega_id, 0)
        return True

    def desativar(self, mega_id: int) -> bool:
        return self.senhas.pop(mega_id, None) is not None

    def ajustar(self, **campos) -> bool:
        if "alarme" in campos:
            self.alarme_porta_s = float(campos["alarme"])
        return True

    def tick(self, agora: float) -> None:
        if self.e == "LIBERADO" and agora - self.desde >= TRAVA_MAX_S:
            self._ev("LIBERACAO_EXPIROU", self.u, 0)
            self.u = 0
            self._ir("OCIOSO")
        elif self.e == "AGUARDANDO_NOTEBOOK" and agora - self.desde >= AGUARDA_NOTEBOOK_S:
            self._ev("CANCELADO", self.u, 1)
            self.u = 0
            self._ir("OCIOSO")
        elif self.e == "PORTA_ABERTA" and not self.aviso_tempo and agora - self.desde >= self.alarme_porta_s:
            self.aviso_tempo = True
            self._ev("PORTA_ABERTA_TEMPO", self.u, int(self.alarme_porta_s))
        elif self.e == "BLOQUEADO" and agora - self.desde >= BLOQUEIO_S:
            self.erros = 0
            self._ir("OCIOSO")
