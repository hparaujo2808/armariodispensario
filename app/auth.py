"""Senhas do PAINEL (farmácia, logística, TI), no notebook.

A digital e a senha de quem abre a porta ficam no Arduino Mega (firmware).
Aqui: scrypt (N=2^14, r=8, p=1) com sal aleatório, comparação em tempo
constante e bloqueio temporário depois de N senhas erradas.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Callable, Optional, Tuple

from .storage import Banco

N, R_, P_ = 2 ** 14, 8, 1


def gerar_hash(senha: str) -> str:
    sal = os.urandom(16)
    h = hashlib.scrypt(senha.encode(), salt=sal, n=N, r=R_, p=P_, dklen=32)
    return f"scrypt${N}${R_}${P_}${sal.hex()}${h.hex()}"


def conferir_hash(senha: str, armazenado: Optional[str]) -> bool:
    if not armazenado:
        return False
    try:
        _, n, r, p, sal, h = armazenado.split("$")
        calc = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(calc.hex(), h)
    except (ValueError, TypeError):
        return False


def validar_politica(senha: str) -> None:
    if len(senha) < 6:
        raise ValueError("a senha deve ter pelo menos 6 caracteres")
    if len(set(senha)) < 3:
        raise ValueError("senha muito simples (use pelo menos 3 caracteres diferentes)")


class Autenticador:
    def __init__(self, banco: Banco, max_tentativas: int = 5, bloqueio_s: int = 300,
                 relogio: Callable[[], float] = time.time):
        self.db = banco
        self.max_tentativas = max_tentativas
        self.bloqueio_s = bloqueio_s
        self.agora = relogio        # o mesmo relógio do núcleo (no legado era time.time(): teste quebrado)

    def por_senha(self, matricula: str, senha: str) -> Tuple[Optional[dict], str]:
        u = self.db.usuario(matricula=matricula)
        if not u or not u["ativo"]:
            self.db.auditar("AUTH_FALHA", {"metodo": "senha", "matricula": matricula, "motivo": "usuario_invalido"})
            return None, "Matrícula ou senha inválida"
        agora = self.agora()
        if u["bloqueado_ate"] > agora:
            self.db.auditar("AUTH_BLOQUEADO", {"metodo": "senha"}, usuario_id=u["id"])
            return None, f"Usuário bloqueado por {int(u['bloqueado_ate'] - agora)} s"
        if conferir_hash(senha, u["senha_hash"]):
            self.db.atualizar_usuario(u["id"], tentativas=0, bloqueado_ate=0)
            self.db.auditar("AUTH_OK", {"metodo": "senha"}, usuario_id=u["id"])
            return u, "ok"
        tent = u["tentativas"] + 1
        campos = {"tentativas": tent}
        if tent >= self.max_tentativas:
            campos.update(tentativas=0, bloqueado_ate=agora + self.bloqueio_s)
        self.db.atualizar_usuario(u["id"], **campos)
        self.db.auditar("AUTH_FALHA", {"metodo": "senha", "tentativa": tent, "motivo": "senha_incorreta"}, usuario_id=u["id"])
        return None, "Matrícula ou senha inválida"
