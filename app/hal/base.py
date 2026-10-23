"""Interface do controlador da porta (o Arduino Mega).

O núcleo (core.py) só conversa com esta interface. Implementações:
  - hal/serial_mega.py : o Mega de verdade, pela USB
  - hal/mega_simulado.py : simulador em Python (demonstração sem hardware e testes)

Os eventos do Mega chegam por `eventos()` (podem vir repetidos: o Mega reenvia até o
ACK, e quem descarta os repetidos é o núcleo) e só são confirmados (`confirmar(seq)`,
cumulativo) depois que o núcleo gravou na auditoria.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple


class Mega:
    online: bool = False

    def eventos(self) -> List[dict]:
        """Eventos recebidos desde a última chamada: {seq, t, u, v, ms, b}."""
        raise NotImplementedError

    def confirmar(self, seq: int) -> None:
        raise NotImplementedError

    def estado(self) -> Dict[str, str]:
        """Última linha ST: {e: estado, u: usuário, pend: eventos pendentes}."""
        raise NotImplementedError

    def relogio(self) -> Optional[Tuple[float, int, int]]:
        """(hora do notebook, boot, ms) da última linha ST: serve para datar eventos guardados."""
        return None

    def temperaturas(self) -> Dict[str, Optional[float]]:
        """Última linha TEMP convertida: baia, cooler1, cooler2 (°C ou None), peltier1/2, alarme, v12."""
        raise NotImplementedError

    # comandos (devolvem True se o Mega respondeu OK)
    def liberar(self, mega_id: int) -> bool:
        raise NotImplementedError

    def cancelar(self) -> bool:
        raise NotImplementedError

    def cadastrar_digital(self, mega_id: int) -> bool:
        raise NotImplementedError

    def definir_senha(self, mega_id: int, senha: str) -> bool:
        raise NotImplementedError

    def desativar(self, mega_id: int) -> bool:
        raise NotImplementedError

    def ajustar(self, **campos) -> bool:
        """SET: sp (décimos °C), vol (0–100), alarme (s), mapa (ex. "012")."""
        raise NotImplementedError

    def tick(self, agora: float) -> None:
        pass

    def fechar(self) -> None:
        pass


def temperaturas_de(campos: Dict[str, str]) -> Dict[str, Optional[float]]:
    ok = campos.get("ok", "000").ljust(3, "0")

    def t(chave, i):
        try:
            return int(campos[chave]) / 10 if ok[i] == "1" else None
        except (KeyError, ValueError):
            return None

    return {"baia": t("baia", 0), "cooler1": t("q1", 1), "cooler2": t("q2", 2),
            "peltier1": campos.get("p1") == "1", "peltier2": campos.get("p2") == "1",
            "alarme": campos.get("al") == "1", "v12": int(campos.get("v12", 0)) / 1000}
