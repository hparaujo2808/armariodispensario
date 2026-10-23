"""O Arduino Mega de verdade, pela USB (pyserial).

Uma thread lê as linhas, confere o CRC e guarda: eventos (fila), estado (ST),
temperaturas (TEMP) e respostas (OK/ERRO). Outra parte manda PING a cada
segundo — é assim que o Mega sabe que o notebook está vivo.

Abrir a porta serial reinicia o Mega (DTR): isso é esperado e seguro (o Mega
volta com a trava desligada). Por isso a porta é aberta uma vez só e mantida.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Dict, List, Optional

import serial
from serial.tools import list_ports

from .. import protocolo as P
from .base import Mega, temperaturas_de

log = logging.getLogger(__name__)

VIDS_ARDUINO = {0x2341, 0x2A03, 0x1A86}     # Arduino, Arduino.org e clones com CH340


def achar_porta() -> Optional[str]:
    for p in list_ports.comports():
        if p.vid in VIDS_ARDUINO:
            return p.device
    return None


class MegaSerial(Mega):
    def __init__(self, porta: str = "auto", baud: int = 115200):
        self.porta = porta
        self.baud = baud
        self.ser: Optional[serial.Serial] = None
        self._fila: "queue.Queue[dict]" = queue.Queue()
        self._respostas: Dict[int, Dict[str, str]] = {}
        self._cond = threading.Condition()
        self._estado: Dict[str, str] = {}
        self._temp: Dict[str, object] = {}
        self._relogio = None
        self._ultima_linha = 0.0
        self._id = 0
        self._parar = threading.Event()
        self._lock_escrita = threading.Lock()
        self._thread = threading.Thread(target=self._laco, name="mega-serial", daemon=True)
        self._thread.start()

    @property
    def online(self) -> bool:
        return time.time() - self._ultima_linha < 5

    # ------------------------------------------------------------- conexão
    def _conectar(self) -> None:
        porta = achar_porta() if self.porta == "auto" else self.porta
        if not porta:
            raise serial.SerialException("Arduino Mega não encontrado em nenhuma porta USB")
        self.ser = serial.Serial(porta, self.baud, timeout=0.2)
        log.info("conectado ao Mega em %s", porta)
        time.sleep(2.0)                      # o Mega reinicia ao abrir a porta
        self._enviar("HELLO")

    def _laco(self) -> None:
        buf = b""
        ultimo_ping = 0.0
        while not self._parar.is_set():
            try:
                if self.ser is None:
                    self._conectar()
                agora = time.time()
                if agora - ultimo_ping >= 1.0:
                    ultimo_ping = agora
                    self._enviar("PING")
                buf += self.ser.read(256)
                while b"\n" in buf:
                    linha, buf = buf.split(b"\n", 1)
                    try:
                        self._tratar(linha.decode("ascii", "replace"))
                    except Exception:   # noqa: BLE001 — uma linha estranha não pode matar a thread (e os PING)
                        log.exception("Mega: linha ignorada %r", linha[:80])
            except (serial.SerialException, OSError) as e:
                log.warning("Mega: %s (tentando de novo em 3 s)", e)
                if self.ser:
                    try:
                        self.ser.close()
                    except OSError:
                        pass
                self.ser = None
                time.sleep(3.0)

    def _tratar(self, linha: str) -> None:
        r = P.analisar(linha)
        if not r:
            return
        tipo, campos = r
        self._ultima_linha = time.time()
        if tipo == "EV":
            self._fila.put(P.evento(campos))
        elif tipo == "ST":
            self._estado = campos
            if "ms" in campos and "b" in campos:
                self._relogio = (time.time(), int(campos["b"]), int(campos["ms"]))
        elif tipo == "TEMP":
            self._temp = temperaturas_de(campos)
        elif tipo in ("OK", "ERRO"):
            with self._cond:
                self._respostas[int(campos.get("id", 0))] = {"ok": tipo == "OK", **campos}
                self._cond.notify_all()

    def _enviar(self, corpo: str) -> None:
        if self.ser is None:
            raise serial.SerialException("Mega desconectado")
        with self._lock_escrita:
            self.ser.write(P.empacotar(corpo))

    def _comando(self, corpo: str, espera: float = 2.0) -> bool:
        with self._cond:
            self._id = self._id % 30000 + 1
            cid = self._id
        try:
            self._enviar(f"{corpo.split()[0]} id={cid}" + "".join(" " + x for x in corpo.split()[1:]))
        except serial.SerialException:
            return False
        fim = time.time() + espera
        with self._cond:
            while cid not in self._respostas and time.time() < fim:
                self._cond.wait(fim - time.time())
            r = self._respostas.pop(cid, None)
        return bool(r and r["ok"])

    # ------------------------------------------------------------ interface
    def eventos(self) -> List[dict]:
        out = []
        while True:
            try:
                out.append(self._fila.get_nowait())
            except queue.Empty:
                return out

    def confirmar(self, seq: int) -> None:
        try:
            self._enviar(f"ACK seq={seq}")
        except serial.SerialException:
            pass

    def estado(self):
        return dict(self._estado)

    def relogio(self):
        return self._relogio

    def temperaturas(self):
        return dict(self._temp)

    def liberar(self, mega_id: int) -> bool:
        return self._comando(f"LIB u={mega_id}")

    def cancelar(self) -> bool:
        return self._comando("CANC")

    def cadastrar_digital(self, mega_id: int) -> bool:
        return self._comando(f"CAD u={mega_id}")

    def definir_senha(self, mega_id: int, senha: str) -> bool:
        return self._comando(f"SENHA u={mega_id} pin={senha}")

    def desativar(self, mega_id: int) -> bool:
        return self._comando(f"DEL u={mega_id}")

    def ajustar(self, **campos) -> bool:
        return self._comando("SET " + " ".join(f"{k}={v}" for k, v in campos.items()))

    def fechar(self) -> None:
        self._parar.set()
        if self.ser:
            self.ser.close()
